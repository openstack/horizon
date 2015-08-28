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
from django.core.urlresolvers import reverse_lazy
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

import six

from horizon import exceptions
from horizon import forms as horizon_forms
from horizon import tables as horizon_tables
from horizon import tabs as horizon_tabs
from horizon.utils import memoized
from horizon import workflows as horizon_workflows

from openstack_dashboard.contrib.trove import api
from openstack_dashboard.contrib.trove.content.databases import forms
from openstack_dashboard.contrib.trove.content.databases import tables
from openstack_dashboard.contrib.trove.content.databases import tabs
from openstack_dashboard.contrib.trove.content.databases import workflows

from openstack_dashboard.dashboards.project.instances \
    import utils as instance_utils


LOG = logging.getLogger(__name__)


class IndexView(horizon_tables.DataTableView):
    table_class = tables.InstancesTable
    template_name = 'project/databases/index.html'
    page_title = _("Instances")

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
        return SortedDict((six.text_type(flavor.id), flavor)
                          for flavor in flavors)

    def _extra_data(self, instance):
        flavor = self.get_flavors().get(instance.flavor["id"])
        if flavor is not None:
            instance.full_flavor = flavor
        instance.host = tables.get_host(instance)
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
    page_title = _("Launch Database")

    def get_initial(self):
        initial = super(LaunchInstanceView, self).get_initial()
        initial['project_id'] = self.request.user.project_id
        initial['user_id'] = self.request.user.id
        return initial


class DetailView(horizon_tabs.TabbedTableView):
    tab_group_class = tabs.InstanceDetailTabs
    template_name = 'project/databases/detail.html'
    page_title = _("Instance Details: {{ instance.name }}")

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        instance = self.get_data()
        table = tables.InstancesTable(self.request)
        context["instance"] = instance
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(instance)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            LOG.info("Obtaining instance for detailed view ")
            instance_id = self.kwargs['instance_id']
            instance = api.trove.instance_get(self.request, instance_id)
            instance.host = tables.get_host(instance)
        except Exception:
            msg = _('Unable to retrieve details '
                    'for database instance: %s') % instance_id
            exceptions.handle(self.request, msg,
                              redirect=self.get_redirect_url())
        try:
            instance.full_flavor = api.trove.flavor_get(
                self.request, instance.flavor["id"])
        except Exception:
            LOG.error('Unable to retrieve flavor details'
                      ' for database instance: %s' % instance_id)
        return instance

    def get_tabs(self, request, *args, **kwargs):
        instance = self.get_data()
        return self.tab_group_class(request, instance=instance, **kwargs)

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:project:databases:index')


class ResizeVolumeView(horizon_forms.ModalFormView):
    form_class = forms.ResizeVolumeForm
    template_name = 'project/databases/resize_volume.html'
    success_url = reverse_lazy('horizon:project:databases:index')
    page_title = _("Resize Database Volume")

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        instance_id = self.kwargs['instance_id']
        try:
            return api.trove.instance_get(self.request, instance_id)
        except Exception:
            msg = _('Unable to retrieve instance details.')
            redirect = reverse('horizon:project:databases:index')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(ResizeVolumeView, self).get_context_data(**kwargs)
        context['instance_id'] = self.kwargs['instance_id']
        return context

    def get_initial(self):
        instance = self.get_object()
        return {'instance_id': self.kwargs['instance_id'],
                'orig_size': instance.volume.get('size', 0)}


class ResizeInstanceView(horizon_forms.ModalFormView):
    form_class = forms.ResizeInstanceForm
    template_name = 'project/databases/resize_instance.html'
    success_url = reverse_lazy('horizon:project:databases:index')
    page_title = _("Resize Database Instance")

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        instance_id = self.kwargs['instance_id']

        try:
            instance = api.trove.instance_get(self.request, instance_id)
            flavor_id = instance.flavor['id']
            flavors = {}
            for i, j in self.get_flavors():
                flavors[str(i)] = j

            if flavor_id in flavors:
                instance.flavor_name = flavors[flavor_id]
            else:
                flavor = api.trove.flavor_get(self.request, flavor_id)
                instance.flavor_name = flavor.name
            return instance
        except Exception:
            redirect = reverse('horizon:project:databases:index')
            msg = _('Unable to retrieve instance details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(ResizeInstanceView, self).get_context_data(**kwargs)
        context['instance_id'] = self.kwargs['instance_id']
        return context

    @memoized.memoized_method
    def get_flavors(self, *args, **kwargs):
        try:
            flavors = api.trove.flavor_list(self.request)
            return instance_utils.sort_flavor_list(self.request, flavors)
        except Exception:
            redirect = reverse("horizon:project:databases:index")
            exceptions.handle(self.request,
                              _('Unable to retrieve flavors.'),
                              redirect=redirect)

    def get_initial(self):
        initial = super(ResizeInstanceView, self).get_initial()
        obj = self.get_object()
        if obj:
            initial.update({'instance_id': self.kwargs['instance_id'],
                            'old_flavor_id': obj.flavor['id'],
                            'old_flavor_name': getattr(obj,
                                                       'flavor_name', ''),
                            'flavors': self.get_flavors()})
        return initial
