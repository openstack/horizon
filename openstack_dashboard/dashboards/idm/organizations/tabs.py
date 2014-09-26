from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.api import keystone
from openstack_dashboard import policy
from openstack_dashboard.dashboards.idm.organizations import tables

from openstack_dashboard.dashboards.idm.organizations \
    import tables as organization_tables


class TenantsTab(tabs.TableTab):
    name = _("Other")
    slug = "tenants_tab"
    table_classes = (tables.TenantsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def has_more_data(self, table):
        return self._more

    def get_tenants_data(self):
        tenants = []
        marker = self.request.GET.get(
            organization_tables.TenantsTable._meta.pagination_param, None)
        domain_context = self.request.session.get('domain_context', None)
        if policy.check((("idm", "idm:list_organizations"),),
                        self.request):
            try:
                tenants, self._more = api.keystone.tenant_list(
                    self.request,
                    domain=domain_context,
                    paginate=True,
                    marker=marker)
            except Exception:
                self._more = False
                exceptions.handle(self.request,
                                  _("Unable to retrieve organization list."))
        elif policy.check((("idm", "idm:list_user_organizations"),),
                          self.request):
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
        else:
            self._more = False
            msg = \
                _("Insufficient privilege level to view organization information.")
            messages.info(self.request, msg)
        return tenants

class MyTenantsTab(tabs.TableTab):
    name = _("Owned")
    slug = "my_tenants_tab"
    table_classes = (tables.MyTenantsTable,)
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
        return tenants

        

class PanelTabs(tabs.TabGroup):
    slug = "panel_tabs"
    tabs = (MyTenantsTab, TenantsTab)
    sticky = True