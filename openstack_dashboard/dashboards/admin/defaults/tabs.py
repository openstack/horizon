# Copyright 2013 Kylin, Inc.
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

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.defaults import tables


class ComputeQuotasTab(tabs.TableTab):
    table_classes = (tables.ComputeQuotasTable,)
    name = _("Compute Quotas")
    slug = "compute_quotas"
    template_name = ("horizon/common/_detail_table.html")

    def get_compute_quotas_data(self):
        request = self.tab_group.request
        tenant_id = request.user.tenant_id
        try:
            data = api.nova.default_quota_get(request, tenant_id)
        except Exception:
            data = []
            exceptions.handle(self.request,
                              _('Unable to get nova quota info.'))
        return data

    def allowed(self, request):
        return api.base.is_service_enabled(request, 'compute')


class VolumeQuotasTab(tabs.TableTab):
    table_classes = (tables.VolumeQuotasTable,)
    name = _("Volume Quotas")
    slug = "volume_quotas"
    template_name = ("horizon/common/_detail_table.html")

    def get_volume_quotas_data(self):
        request = self.tab_group.request
        tenant_id = request.user.tenant_id
        try:
            data = api.cinder.default_quota_get(request, tenant_id)
        except Exception:
            data = []
            exceptions.handle(self.request,
                              _('Unable to get cinder quota info.'))
        return data

    def allowed(self, request):
        return api.cinder.is_volume_service_enabled(request)


class NetworkQuotasTab(tabs.TableTab):
    table_classes = (tables.NetworkQuotasTable,)
    name = _("Network Quotas")
    slug = "network_quotas"
    template_name = ("horizon/common/_detail_table.html")

    def get_network_quotas_data(self):
        request = self.tab_group.request
        try:
            data = api.neutron.default_quota_get(request)
        except Exception:
            data = []
            exceptions.handle(self.request,
                              _('Unable to get neutron quota info.'))
        return data

    def allowed(self, request):
        return api.base.is_service_enabled(request, 'network')


class DefaultsTabs(tabs.TabGroup):
    slug = "defaults"
    tabs = (ComputeQuotasTab, VolumeQuotasTab, NetworkQuotasTab)
    sticky = True
