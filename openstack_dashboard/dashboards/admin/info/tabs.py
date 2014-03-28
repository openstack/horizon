# Copyright 2012 Nebula, Inc.
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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard.api import base
from openstack_dashboard.api import keystone
from openstack_dashboard.api import neutron
from openstack_dashboard.api import nova
from openstack_dashboard.usage import quotas

from openstack_dashboard.dashboards.admin.info import constants
from openstack_dashboard.dashboards.admin.info import tables


class ServicesTab(tabs.TableTab):
    table_classes = (tables.ServicesTable,)
    name = _("Services")
    slug = "services"
    template_name = constants.INFO_DETAIL_TEMPLATE_NAME

    def get_services_data(self):
        request = self.tab_group.request
        services = []
        for i, service in enumerate(request.user.service_catalog):
            service['id'] = i
            services.append(
                keystone.Service(service, request.user.services_region))
        return services


class NovaServicesTab(tabs.TableTab):
    table_classes = (tables.NovaServicesTable,)
    name = _("Compute Services")
    slug = "nova_services"
    template_name = constants.INFO_DETAIL_TEMPLATE_NAME

    def get_nova_services_data(self):
        try:
            services = nova.service_list(self.tab_group.request)
        except Exception:
            msg = _('Unable to get nova services list.')
            exceptions.check_message(["Connection", "refused"], msg)
            raise

        return services


class NetworkAgentsTab(tabs.TableTab):
    table_classes = (tables.NetworkAgentsTable,)
    name = _("Network Agents")
    slug = "network_agents"
    template_name = constants.INFO_DETAIL_TEMPLATE_NAME

    def allowed(self, request):
        return base.is_service_enabled(request, 'network')

    def get_network_agents_data(self):
        try:
            agents = neutron.agent_list(self.tab_group.request)
        except Exception:
            msg = _('Unable to get network agents list.')
            exceptions.check_message(["Connection", "refused"], msg)
            raise

        return agents


class DefaultQuotasTab(tabs.TableTab):
    table_classes = (tables.QuotasTable,)
    name = _("Default Quotas")
    slug = "quotas"
    template_name = constants.INFO_DETAIL_TEMPLATE_NAME

    def get_quotas_data(self):
        request = self.tab_group.request
        try:
            data = quotas.get_default_quota_data(request)
        except Exception:
            data = []
            exceptions.handle(self.request, _('Unable to get quota info.'))
        return data


class SystemInfoTabs(tabs.TabGroup):
    slug = "system_info"
    tabs = (ServicesTab, NovaServicesTab,
            NetworkAgentsTab, DefaultQuotasTab)
    sticky = True
