# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Policy engine for Horizon"""

import logging
import os.path

from django.conf import settings
from openstack_auth import utils as auth_utils
from oslo.config import cfg

from openstack_dashboard.openstack.common import policy


LOG = logging.getLogger(__name__)

CONF = cfg.CONF
# Policy Enforcer has been updated to take in a policy directory
# as a config option. However, the default value in is set to
# ['policy.d'] which causes the code to break. Set the default
# value to empty list for now.
CONF.policy_dirs = []

_ENFORCER = None
_BASE_PATH = getattr(settings, 'POLICY_FILES_PATH', '')


def _get_enforcer():
    global _ENFORCER
    if not _ENFORCER:
        _ENFORCER = {}
        policy_files = getattr(settings, 'POLICY_FILES', {})
        for service in policy_files.keys():
            enforcer = policy.Enforcer()
            enforcer.policy_path = os.path.join(_BASE_PATH,
                                                policy_files[service])
            if os.path.isfile(enforcer.policy_path):
                LOG.debug("adding enforcer for service: %s" % service)
                _ENFORCER[service] = enforcer
            else:
                LOG.warn("policy file for service: %s not found at %s" %
                         (service, enforcer.policy_path))
    return _ENFORCER


def reset():
    global _ENFORCER
    _ENFORCER = None


def check(actions, request, target=None):
    """Check user permission.

    Check if the user has permission to the action according
    to policy setting.

    :param actions: list of scope and action to do policy checks on,
        the composition of which is (scope, action)

        * scope: service type managing the policy for action

        * action: string representing the action to be checked

            this should be colon separated for clarity.
            i.e.

                | compute:create_instance
                | compute:attach_volume
                | volume:attach_volume

        for a policy action that requires a single action, actions
        should look like

            | "(("compute", "compute:create_instance"),)"

        for a multiple action check, actions should look like
            | "(("identity", "identity:list_users"),
            |   ("identity", "identity:list_roles"))"

    :param request: django http request object. If not specified, credentials
                    must be passed.
    :param target: dictionary representing the object of the action
                      for object creation this should be a dictionary
                      representing the location of the object e.g.
                      {'project_id': object.project_id}
    :returns: boolean if the user has permission or not for the actions.
    """
    if target is None:
        target = {}
    user = auth_utils.get_user(request)

    # Several service policy engines default to a project id check for
    # ownership. Since the user is already scoped to a project, if a
    # different project id has not been specified use the currently scoped
    # project's id.
    #
    # The reason is the operator can edit the local copies of the service
    # policy file. If a rule is removed, then the default rule is used. We
    # don't want to block all actions because the operator did not fully
    # understand the implication of editing the policy file. Additionally,
    # the service APIs will correct us if we are too permissive.
    if target.get('project_id') is None:
        target['project_id'] = user.project_id
    # same for user_id
    if target.get('user_id') is None:
        target['user_id'] = user.id
    # same for domain_id
    if target.get('domain_id') is None:
        target['domain_id'] = user.domain_id

    credentials = _user_to_credentials(request, user)

    enforcer = _get_enforcer()

    for action in actions:
        scope, action = action[0], action[1]
        if scope in enforcer:
            # if any check fails return failure
            if not enforcer[scope].enforce(action, target, credentials):
                # to match service implementations, if a rule is not found,
                # use the default rule for that service policy
                #
                # waiting to make the check because the first call to
                # enforce loads the rules
                if action not in enforcer[scope].rules:
                    if not enforcer[scope].enforce('default',
                                                   target, credentials):
                        return False
                else:
                    return False
        # if no policy for scope, allow action, underlying API will
        # ultimately block the action if not permitted, treat as though
        # allowed
    return True


def _user_to_credentials(request, user):
    if not hasattr(user, "_credentials"):
        roles = [role['name'] for role in user.roles]
        user._credentials = {'user_id': user.id,
                             'token': user.token,
                             'username': user.username,
                             'project_id': user.project_id,
                             'project_name': user.project_name,
                             'domain_id': user.user_domain_id,
                             'is_admin': user.is_superuser,
                             'roles': roles}
    return user._credentials


class PolicyTargetMixin(object):
    """Mixin that adds the get_policy_target function

    policy_target_attrs - a tuple of tuples which defines
        the relationship between attributes in the policy
        target dict and attributes in the passed datum object.
        policy_target_attrs can be overwritten by sub-classes
        which do not use the default, so they can neatly define
        their policy target information, without overriding the
        entire get_policy_target function.
    """

    policy_target_attrs = (("project_id", "tenant_id"),
                           ("user_id", "user_id"),
                           ("domain_id", "domain_id"))

    def get_policy_target(self, request, datum=None):
        policy_target = {}
        for policy_attr, datum_attr in self.policy_target_attrs:
            if datum:
                policy_target[policy_attr] = getattr(datum, datum_attr, None)
            else:
                policy_target[policy_attr] = None
        return policy_target
