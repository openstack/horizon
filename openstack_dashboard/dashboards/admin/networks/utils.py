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

from horizon import exceptions

from openstack_dashboard import api


def is_dhcp_agent_scheduler_supported(request):
    try:
        if api.neutron.is_extension_supported(
                request, 'dhcp_agent_scheduler'):
            return True
    except Exception:
        msg = _("Unable to check if DHCP agent scheduler "
                "extension is supported")
        exceptions.handle(request, msg)
    return False
