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
from horizon import messages
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard import policy
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm.organizations \
    import tables as organization_tables


class TenantsTab(tabs.TableTab):
    name = _("Other")
    slug = "tenants_tab"
    table_classes = (organization_tables.TenantsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def has_more_data(self, table):
        return self._more

    def get_tenants_data(self):
        tenants = []
        my_tenants = []
        #domain_context = self.request.session.get('domain_context', None)
        try:
            tenants, self._more = api.keystone.tenant_list(self.request,
                                                            admin=False)
            my_tenants, _more = api.keystone.tenant_list(self.request,
                                            user=self.request.user.id,
                                            admin=False)
            tenants = [t for t in tenants if not t in my_tenants]
        except Exception as e:
            self._more = False
            exceptions.handle(self.request,
                              _("Unable to retrieve organization list. \
                                    Error message: {0}".format(e)))
        return idm_utils.filter_default_organizations(tenants)
        # if policy.check((("idm", "idm:list_organizations"),),
        #                 self.request):
        #     try:
        #         tenants, self._more = api.keystone.tenant_list(
        #             self.request,
        #             domain=domain_context,
        #             paginate=True,
        #             marker=marker)
        #     except Exception:
        #         self._more = False
        #         exceptions.handle(self.request,
        #                           _("Unable to retrieve organization list."))
        # elif policy.check((("idm", "idm:list_user_organizations"),),
        #                   self.request):
        #     try:
        #         tenants, self._more = api.keystone.tenant_list(
        #             self.request,
        #             user=self.request.user.id,
        #             paginate=True,
        #             marker=marker,
        #             admin=False)
        #     except Exception:
        #         self._more = False
        #         exceptions.handle(self.request,
        #                           _("Unable to retrieve organization information."))
        # else:
        #     self._more = False
        #     msg = \
        #         _("Insufficient privilege level to view organization information.")
        #     messages.info(self.request, msg)
        # return idm_utils.filter_default_organizations(self.request.user, tenants)


class MyTenantsTab(tabs.TableTab):
    name = _("Owned")
    slug = "my_tenants_tab"
    table_classes = (organization_tables.MyTenantsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def has_more_data(self, table):
        return self._more

    def get_mytenants_data(self):
        tenants = []
        marker = self.request.GET.get(
            organization_tables.MyTenantsTable._meta.pagination_param, None)
        domain_context = self.request.session.get('domain_context', None)
        try:
            tenants, self._more = api.keystone.tenant_list(
                self.request,
                user=self.request.user.id,
                paginate=True,
                marker=marker,
                admin=False)
        except Exception:
            self._more = False
            exceptions.handle(self.request,
                              _("Unable to retrieve organization information."))
        return idm_utils.filter_default_organizations(tenants)


class PanelTabs(tabs.TabGroup):
    slug = "panel_tabs"
    tabs = (MyTenantsTab, TenantsTab)
    sticky = True