# Copyright 2013 B1 Systems GmbH
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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon import tabs
from horizon.utils import functions as utils

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.hypervisors \
    import tables as project_tables
from openstack_dashboard.dashboards.admin.hypervisors \
    import tabs as project_tabs


class AdminIndexView(tabs.TabbedTableView):
    tab_group_class = project_tabs.HypervisorHostTabs
    template_name = 'admin/hypervisors/index.html'
    page_title = _("All Hypervisors")

    def get_data(self):
        hypervisors = []
        try:
            hypervisors = api.nova.hypervisor_list(self.request)
            hypervisors.sort(key=utils.natural_sort('hypervisor_hostname'))
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve hypervisor information.'))

        return hypervisors

    def get_context_data(self, **kwargs):
        context = super(AdminIndexView, self).get_context_data(**kwargs)
        try:
            context["stats"] = api.nova.hypervisor_stats(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve hypervisor statistics.'))

        return context


class AdminDetailView(tables.DataTableView):
    table_class = project_tables.AdminHypervisorInstancesTable
    template_name = 'admin/hypervisors/detail.html'
    page_title = _("Servers")

    def get_data(self):
        instances = []
        try:
            id, name = self.kwargs['hypervisor'].split('_', 1)
            result = api.nova.hypervisor_search(self.request,
                                                name)
            for hypervisor in result:
                if str(hypervisor.id) == id:
                    try:
                        instances += hypervisor.servers
                    except AttributeError:
                        pass
        except Exception:
            exceptions.handle(
                self.request,
                _('Unable to retrieve hypervisor instances list.'))
        return instances

    def get_context_data(self, **kwargs):
        context = super(AdminDetailView, self).get_context_data(**kwargs)
        hypervisor_name = self.kwargs['hypervisor'].split('_', 1)[1]
        breadcrumb = [
            (_("Hypervisors"), reverse('horizon:admin:hypervisors:index')),
            (hypervisor_name,), ]
        context['custom_breadcrumb'] = breadcrumb
        return context
