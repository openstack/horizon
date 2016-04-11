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
from openstack_dashboard.api import cinder
from openstack_dashboard.api import heat
from openstack_dashboard.api import keystone
from openstack_dashboard.api import neutron
from openstack_dashboard.api import nova
from openstack_dashboard.dashboards.admin.info import constants
from openstack_dashboard.dashboards.admin.info import tables


class ServicesTab(tabs.TableTab):
    table_classes = (tables.ServicesTable,)
    name = tables.ServicesTable.Meta.verbose_name
    slug = tables.ServicesTable.Meta.name
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
    name = tables.NovaServicesTable.Meta.verbose_name
    slug = tables.NovaServicesTable.Meta.name
    template_name = constants.INFO_DETAIL_TEMPLATE_NAME
    permissions = ('openstack.services.compute',)

    def get_nova_services_data(self):
        try:
            services = nova.service_list(self.tab_group.request)
        except Exception:
            msg = _('Unable to get nova services list.')
            exceptions.check_message(["Connection", "refused"], msg)
            exceptions.handle(self.request, msg)
            services = []
        return services


class CinderServicesTab(tabs.TableTab):
    table_classes = (tables.CinderServicesTable,)
    name = tables.CinderServicesTable.Meta.verbose_name
    slug = tables.CinderServicesTable.Meta.name
    template_name = constants.INFO_DETAIL_TEMPLATE_NAME
    permissions = (
        ('openstack.services.volume', 'openstack.services.volumev2'),
    )

    def get_cinder_services_data(self):
        try:
            services = cinder.service_list(self.tab_group.request)
        except Exception:
            msg = _('Unable to get cinder services list.')
            exceptions.check_message(["Connection", "refused"], msg)
            exceptions.handle(self.request, msg)
            services = []
        return services


class NetworkAgentsTab(tabs.TableTab):
    table_classes = (tables.NetworkAgentsTable,)
    name = tables.NetworkAgentsTable.Meta.verbose_name
    slug = tables.NetworkAgentsTable.Meta.name
    template_name = constants.INFO_DETAIL_TEMPLATE_NAME

    def allowed(self, request):
        try:
            return (base.is_service_enabled(request, 'network') and
                    neutron.is_extension_supported(request, 'agent'))
        except Exception:
            exceptions.handle(request, _('Unable to get network agents info.'))
            return False

    def get_network_agents_data(self):
        try:
            agents = neutron.agent_list(self.tab_group.request)
        except Exception:
            msg = _('Unable to get network agents list.')
            exceptions.check_message(["Connection", "refused"], msg)
            exceptions.handle(self.request, msg)
            agents = []
        return agents


class HeatServiceTab(tabs.TableTab):
    table_classes = (tables.HeatServiceTable,)
    name = tables.HeatServiceTable.Meta.verbose_name
    slug = tables.HeatServiceTable.Meta.name
    template_name = constants.INFO_DETAIL_TEMPLATE_NAME

    def allowed(self, request):
        try:
            return (base.is_service_enabled(request, 'orchestration'))
        except Exception:
            exceptions.handle(request, _('Orchestration service is disabled.'))
            return False

    def get_heat_services_data(self):
        try:
            services = heat.service_list(self.tab_group.request)
        except Exception:
            msg = _('Unable to get Orchestration service list.')
            exceptions.check_message(["Connection", "refused"], msg)
            exceptions.handle(self.request, msg)
            services = []
        return services


class SystemInfoTabs(tabs.TabGroup):
    slug = "system_info"
    tabs = (ServicesTab, NovaServicesTab, CinderServicesTab,
            NetworkAgentsTab, HeatServiceTab)
    sticky = True
