from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import messages
from horizon import tables
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.api import keystone
from openstack_dashboard import policy

from openstack_dashboard.dashboards.idm.organizations import tables as organization_tables

ORGANIZATION_INFO_FIELDS = ("domain_id",
                           "domain_name",
                           "name",
                           "description",
                           "enabled")

INDEX_URL = "horizon:idm:organizations:index"

class TenantContextMixin(object):
    @memoized.memoized_method
    def get_object(self):
        tenant_id = self.kwargs['tenant_id']
        try:
            return api.keystone.tenant_get(self.request, tenant_id, admin=True)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve project information.'),
                              redirect=reverse(INDEX_URL))

    def get_context_data(self, **kwargs):
        context = super(TenantContextMixin, self).get_context_data(**kwargs)
        context['tenant'] = self.get_object()
        return context

# class IndexView(tables.DataTableView):
    

#     def get_data(self):
#         tenants = []
#         domain_context = self.request.session.get('domain_context', None)
#         if policy.check((("idm", "idm:list_organizations"),),
#                         self.request):
#             try:
#                 tenants = api.keystone.tenant_list(
#                     self.request)
#             except Exception:
#                 exceptions.handle(self.request,
#                                   _("Unable to retrieve organization list."))
#         elif policy.check((("idm", "idm:list_user_organizations"),),
#                           self.request):
#             try:
#                 tenants = api.keystone.tenant_list(
#                     self.request,
#                     user=self.request.user.id)
#             except Exception:
#                 exceptions.handle(self.request,
#                                   _("Unable to retrieve organization information."))
#         else:
#             msg = \
#                 _("Insufficient privilege level to view organization information.")
#             messages.info(self.request, msg)
#         return tenants

class IndexView(tables.DataTableView):
    table_class = organization_tables.TenantsTable
    template_name = 'idm/organizations/index.html'

    def has_more_data(self, table):
        return self._more

    def get_data(self):
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
                                  _("Unable to retrieve project list."))
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
                                  _("Unable to retrieve project information."))
        else:
            self._more = False
            msg = \
                _("Insufficient privilege level to view project information.")
            messages.info(self.request, msg)
        return tenants