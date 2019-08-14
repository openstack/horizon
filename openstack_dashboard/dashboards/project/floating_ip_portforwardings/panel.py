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

from django.utils.translation import gettext_lazy as _

import horizon

from openstack_dashboard.api import neutron

LOG = logging.getLogger(__name__)


class FloatingIpPortforwardingRules(horizon.Panel):
    name = _("Floating IP port forwarding rules")
    slug = 'floating_ip_portforwardings'
    permissions = ('openstack.services.network',)
    nav = False

    def allowed(self, context):
        request = context['request']
        return (
            super().allowed(context) and
            request.user.has_perms(self.permissions) and
            neutron.is_extension_floating_ip_port_forwarding_supported(
                request)
        )
