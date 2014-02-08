# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Rackspace Hosting
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

"""
Views for managing database instances.
"""
import logging

from django.core.urlresolvers import reverse
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables as horizon_tables
from horizon import tabs as horizon_tabs
from horizon.utils import memoized
from horizon import workflows as horizon_workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.databases import tables
from openstack_dashboard.dashboards.project.databases import tabs
from openstack_dashboard.dashboards.project.databases import workflows


LOG = logging.getLogger(__name__)


def get_host(instance):
    if hasattr(instance, "hostname"):
        return instance.hostname
    elif hasattr(instance, "ip") and instance.ip:
        return instance.ip[0]
    return _("Not Assigned")


class IndexView(horizon_tables.DataTableView):
    table_class = tables.InstancesTable
    template_name = 'project/databases/index.html'

    def has_more_data(self, table):
        return self._more

    @memoized.memoized_method
    def get_flavors(self):
        try:
            flavors = api.trove.flavor_list(self.request)
        except Exception:
            flavors = []
            msg = _('Unable to retrieve database size information.')
            exceptions.handle(self.request, msg)
        return SortedDict((unicode(flavor.id), flavor) for flavor in flavors)

    def _extra_data(self, instance):
        flavor = self.get_flavors().get(instance.flavor["id"])
        if flavor is not None:
            instance.full_flavor = flavor
        instance.host = get_host(instance)
        return instance

    def get_data(self):
        marker = self.request.GET.get(
            tables.InstancesTable._meta.pagination_param)
        # Gather our instances
        try:
            instances = api.trove.instance_list(self.request, marker=marker)
            self._more = instances.next or False
        except Exception:
            self._more = False
            instances = []
            msg = _('Unable to retrieve database instances.')
            exceptions.handle(self.request, msg)
        map(self._extra_data, instances)
        return instances


class LaunchInstanceView(horizon_workflows.WorkflowView):
    workflow_class = workflows.LaunchInstance
    template_name = "project/databases/launch.html"

    def get_initial(self):
        initial = super(LaunchInstanceView, self).get_initial()
        initial['project_id'] = self.request.user.project_id
        initial['user_id'] = self.request.user.id
        return initial


class DetailView(horizon_tabs.TabbedTableView):
    tab_group_class = tabs.InstanceDetailTabs
    template_name = 'project/databases/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["instance"] = self.get_data()
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            LOG.info("Obtaining instance for detailed view ")
            instance_id = self.kwargs['instance_id']
            instance = api.trove.instance_get(self.request, instance_id)
            instance.host = get_host(instance)
        except Exception:
            redirect = reverse('horizon:project:databases:index')
            msg = _('Unable to retrieve details '
                    'for database instance: %s') % instance_id
            exceptions.handle(self.request, msg, redirect=redirect)
        try:
            instance.full_flavor = api.trove.flavor_get(
                self.request, instance.flavor["id"])
        except Exception:
            LOG.error('Unable to retrieve flavor details'
                      ' for database instance: %s') % instance_id
        return instance

    def get_tabs(self, request, *args, **kwargs):
        instance = self.get_data()
        return self.tab_group_class(request, instance=instance, **kwargs)
