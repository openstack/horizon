# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging

from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.api import neutron
from openstack_dashboard.utils import settings as setting_utils

LOG = logging.getLogger(__name__)


class RBACPolicies(horizon.Panel):
    name = _("RBAC Policies")
    slug = "rbac_policies"
    permissions = ('openstack.services.network',)
    policy_rules = (("network", "context_is_admin"),)

    def allowed(self, context):
        request = context['request']
        try:
            return (
                setting_utils.get_dict_config(
                    'OPENSTACK_NEUTRON_NETWORK', 'enable_rbac_policy') and
                neutron.is_extension_supported(request,
                                               extension_alias='rbac-policies')
            )
        except Exception:
            LOG.error("Call to list enabled services failed. This is likely "
                      "due to a problem communicating with the Neutron "
                      "endpoint. RBAC Policies panel will not be displayed.")
            return False
