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


LOG = logging.getLogger(__name__)


class ServerGroups(horizon.Panel):
    name = _("Server Groups")
    slug = "server_groups"
    permissions = ('openstack.services.compute',)
    policy_rules = (("compute", "os_compute_api:os-server-groups:index"),)

    def allowed(self, context):
        request = context['request']
        try:
            return (
                super(ServerGroups, self).allowed(context) and
                request.user.has_perms(self.permissions)
            )
        except Exception:
            LOG.exception("Call to list enabled services failed. This is "
                          "likely due to a problem communicating with the "
                          "Nova endpoint. Server Groups panel will not be "
                          "displayed.")
            return False
