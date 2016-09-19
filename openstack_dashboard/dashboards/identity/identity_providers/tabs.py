# Copyright (C) 2015 Yahoo! Inc. All Rights Reserved.
#
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

from django.utils.translation import ugettext_lazy as _

from horizon import tabs


from openstack_dashboard.dashboards.identity.identity_providers.protocols \
    import tables as ptbl


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = "identity/identity_providers/_detail_overview.html"

    def get_context_data(self, request):
        return {
            "identity_provider": self.tab_group.kwargs['identity_provider']
        }


class ProtocolsTab(tabs.TableTab):
    table_classes = (ptbl.ProtocolsTable,)
    name = _("Protocols")
    slug = "protocols"
    template_name = "horizon/common/_detail_table.html"

    def get_idp_protocols_data(self):
        return self.tab_group.kwargs['protocols']


class IdPDetailTabs(tabs.DetailTabsGroup):
    slug = "idp_details"
    tabs = (OverviewTab, ProtocolsTab)
    sticky = True
