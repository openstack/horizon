from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import messages
from horizon import tables

from openstack_dashboard.dashboards.idm.applications import tables as home_tables



class IndexView(tables.DataTableView):
    table_class = home_tables.ApplicationsTable
    template_name = 'idm/applications/index.html'

    def get_data(self):
        tenants = []
        marker = self.request.GET.get(
            home_tables.ApplicationsTable._meta.pagination_param, None)
        domain_context = self.request.session.get('domain_context', None)
        
        return tenants