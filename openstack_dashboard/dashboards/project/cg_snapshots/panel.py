# Copyright 2017 Rackspace, Inc.
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

import logging

from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard import api
from openstack_dashboard import policy

LOG = logging.getLogger(__name__)


class CGSnapshots(horizon.Panel):
    name = _("Consistency Group Snapshots")
    slug = 'cg_snapshots'
    permissions = (
        ('openstack.services.volume', 'openstack.services.volumev2',
         'openstack.services.volumev3'),
    )
    policy_rules = (("volume", "consistencygroup:get_all_cgsnapshots"),)

    def allowed(self, context):
        request = context['request']
        try:
            return (
                super(CGSnapshots, self).allowed(context) and
                request.user.has_perms(self.permissions) and
                policy.check(self.policy_rules, request) and
                api.cinder.get_microversion(request, 'consistency_groups') and
                not api.cinder.get_microversion(request, 'groups')
            )
        except Exception:
            LOG.error("Call to list enabled services failed. This is likely "
                      "due to a problem communicating with the Cinder "
                      "endpoint. Consistency Group Snapshot panel will not be "
                      "displayed.")
            return False
