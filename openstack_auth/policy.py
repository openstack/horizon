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

"""Policy engine for openstack_auth"""

import logging
import os.path

from django.conf import settings
from oslo_config import cfg
from oslo_policy import opts as policy_opts
from oslo_policy import policy

from openstack_auth import user as auth_user
from openstack_auth import utils as auth_utils

LOG = logging.getLogger(__name__)

_ENFORCER = None
_BASE_PATH = settings.POLICY_FILES_PATH


def _get_policy_conf(policy_file, policy_dirs=None):
    conf = cfg.ConfigOpts()
    # Passing [] is required. Otherwise oslo.config looks up sys.argv.
    conf([])
    policy_opts.set_defaults(conf)
    conf.set_default('policy_file', policy_file, 'oslo_policy')
    # Policy Enforcer has been updated to take in a policy directory
    # as a config option. However, the default value in is set to
    # ['policy.d'] which causes the code to break. Set the default
    # value to empty list for now.
    if policy_dirs is None:
        policy_dirs = []
    conf.set_default('policy_dirs', policy_dirs, 'oslo_policy')
    return conf


def _get_policy_file_with_full_path(service):
    policy_files = settings.POLICY_FILES
    policy_file = os.path.join(_BASE_PATH, policy_files[service])
    policy_dirs = settings.POLICY_DIRS.get(service, [])
    policy_dirs = [os.path.join(_BASE_PATH, policy_dir)
                   for policy_dir in policy_dirs]
    return policy_file, policy_dirs


def _get_enforcer():
    global _ENFORCER
    if not _ENFORCER:
        _ENFORCER = {}
        policy_files = settings.POLICY_FILES
        for service in policy_files.keys():
            policy_file, policy_dirs = _get_policy_file_with_full_path(service)
            conf = _get_policy_conf(policy_file, policy_dirs)
            enforcer = policy.Enforcer(conf)
            try:
                enforcer.load_rules()
            except IOError:
                # Just in case if we have permission denied error which is not
                # handled by oslo.policy now. It will handled in the code like
                # we don't have any policy file: allow action from the Horizon
                # side.
                LOG.warning("Cannot load a policy file '%s' for service '%s' "
                            "due to IOError. One possible reason is "
                            "permission denied.", policy_file, service)
            # Ensure enforcer.rules is populated.
            if enforcer.rules:
                LOG.debug("adding enforcer for service: %s", service)
                _ENFORCER[service] = enforcer
            else:
                locations = policy_file
                if policy_dirs:
                    locations += ' and files under %s' % policy_dirs
                LOG.warning("No policy rules for service '%s' in %s",
                            service, locations)
    return _ENFORCER


def reset():
    global _ENFORCER
    _ENFORCER = None


def check(actions, request, target=None):
    """Check user permission.

    Check if the user has permission to the action according
    to policy setting.

    :param actions: list of scope and action to do policy checks on,
        the composition of which is (scope, action). Multiple actions
        are treated as a logical AND.

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
    if target.get('tenant_id') is None:
        target['tenant_id'] = target['project_id']
    # same for user_id
    if target.get('user_id') is None:
        target['user_id'] = user.id

    domain_id_keys = [
        'domain_id',
        'project.domain_id',
        'user.domain_id',
        'group.domain_id'
    ]
    # populates domain id keys with user's current domain id
    for key in domain_id_keys:
        if target.get(key) is None:
            target[key] = user.user_domain_id

    credentials = _user_to_credentials(user)
    domain_credentials = _domain_to_credentials(request, user)
    # if there is a domain token use the domain_id instead of the user's domain
    if domain_credentials:
        credentials['domain_id'] = domain_credentials.get('domain_id')

    enforcer = _get_enforcer()

    for action in actions:
        scope, action = action[0], action[1]
        if scope in enforcer:
            # this is for handling the v3 policy file and will only be
            # needed when a domain scoped token is present
            if scope == 'identity' and domain_credentials:
                # use domain credentials
                if not _check_credentials(enforcer[scope],
                                          action,
                                          target,
                                          domain_credentials):
                    return False

            # use project credentials
            if not _check_credentials(enforcer[scope],
                                      action, target, credentials):
                return False

        # if no policy for scope, allow action, underlying API will
        # ultimately block the action if not permitted, treat as though
        # allowed
    return True


def _check_credentials(enforcer_scope, action, target, credentials):
    is_valid = True
    if not enforcer_scope.enforce(action, target, credentials):
        # to match service implementations, if a rule is not found,
        # use the default rule for that service policy
        #
        # waiting to make the check because the first call to
        # enforce loads the rules
        if action not in enforcer_scope.rules:
            if not enforcer_scope.enforce('default', target, credentials):
                if 'default' in enforcer_scope.rules:
                    is_valid = False
        else:
            is_valid = False
    return is_valid


def _user_to_credentials(user):
    if not hasattr(user, "_credentials"):
        roles = [role['name'] for role in user.roles]
        user._credentials = {'user_id': user.id,
                             'username': user.username,
                             'project_id': user.project_id,
                             'tenant_id': user.project_id,
                             'project_name': user.project_name,
                             'domain_id': user.user_domain_id,
                             'is_admin': user.is_superuser,
                             'roles': roles}
    return user._credentials


def _domain_to_credentials(request, user):
    if not hasattr(user, "_domain_credentials"):
        try:
            domain_auth_ref = request.session.get('domain_token')

            # no domain role or not running on V3
            if not domain_auth_ref:
                return None
            domain_user = auth_user.create_user_from_token(
                request, auth_user.Token(domain_auth_ref),
                domain_auth_ref.service_catalog.url_for(interface=None))
            user._domain_credentials = _user_to_credentials(domain_user)

            # uses the domain_id associated with the domain_user
            user._domain_credentials['domain_id'] = domain_user.domain_id

        except Exception:
            LOG.warning("Failed to create user from domain scoped token.")
            return None
    return user._domain_credentials
