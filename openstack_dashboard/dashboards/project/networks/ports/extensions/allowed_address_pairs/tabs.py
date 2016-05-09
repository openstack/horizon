# Copyright 2015, Alcatel-Lucent USA Inc.
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

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks.ports.extensions.\
    allowed_address_pairs import tables as addr_pairs_tables


LOG = logging.getLogger(__name__)


class AllowedAddressPairsTab(tabs.TableTab):
    table_classes = (addr_pairs_tables.AllowedAddressPairsTable,)
    name = _("Allowed Address Pairs")
    slug = "allowed_address_pairs"
    template_name = "horizon/common/_detail_table.html"

    def allowed(self, request):
        port = self.tab_group.kwargs['port']
        if not port or not port.get('port_security_enabled', True):
            return False

        try:
            return api.neutron.is_extension_supported(request,
                                                      "allowed-address-pairs")
        except Exception as e:
            LOG.error("Failed to check if Neutron allowed-address-pairs "
                      "extension is supported: %s", e)
            return False

    def get_allowed_address_pairs_data(self):
        port = self.tab_group.kwargs['port']
        return port.get('allowed_address_pairs', [])
