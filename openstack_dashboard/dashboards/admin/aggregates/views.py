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

import json

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.aggregates \
    import constants
from openstack_dashboard.dashboards.admin.aggregates \
    import forms as aggregate_forms
from openstack_dashboard.dashboards.admin.aggregates \
    import tables as project_tables
from openstack_dashboard.dashboards.admin.aggregates \
    import workflows as aggregate_workflows


INDEX_URL = constants.AGGREGATES_INDEX_URL


class IndexView(tables.MultiTableView):
    table_classes = (project_tables.HostAggregatesTable,
                     project_tables.AvailabilityZonesTable)
    template_name = constants.AGGREGATES_TEMPLATE_NAME
    page_title = _("Host Aggregates")

    def get_host_aggregates_data(self):
        request = self.request
        aggregates = []
        try:
            aggregates = api.nova.aggregate_details_list(self.request)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve host aggregates list.'))
        aggregates.sort(key=lambda aggregate: aggregate.name.lower())
        return aggregates

    def get_availability_zones_data(self):
        request = self.request
        availability_zones = []
        try:
            availability_zones = \
                api.nova.availability_zone_list(self.request, detailed=True)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve availability zone list.'))
        availability_zones.sort(key=lambda az: az.zoneName.lower())
        return availability_zones


class CreateView(workflows.WorkflowView):
    workflow_class = aggregate_workflows.CreateAggregateWorkflow
    template_name = constants.AGGREGATES_CREATE_VIEW_TEMPLATE
    page_title = _("Create Host Aggregate")


class UpdateView(forms.ModalFormView):
    template_name = constants.AGGREGATES_UPDATE_VIEW_TEMPLATE
    form_class = aggregate_forms.UpdateAggregateForm
    success_url = reverse_lazy(constants.AGGREGATES_INDEX_URL)
    page_title = _("Edit Host Aggregate")

    def get_initial(self):
        aggregate = self.get_object()
        return {'id': self.kwargs["id"],
                'name': aggregate.name,
                'availability_zone': aggregate.availability_zone}

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['id'] = self.kwargs['id']
        return context

    def get_object(self):
        if not hasattr(self, "_object"):
            aggregate_id = self.kwargs['id']
            try:
                self._object = \
                    api.nova.aggregate_get(self.request, aggregate_id)
            except Exception:
                msg = _('Unable to retrieve the aggregate to be updated')
                exceptions.handle(self.request, msg)
        return self._object


class UpdateMetadataView(forms.ModalFormView):
    template_name = constants.AGGREGATES_UPDATE_METADATA_TEMPLATE
    form_class = aggregate_forms.UpdateMetadataForm
    success_url = reverse_lazy(constants.AGGREGATES_INDEX_URL)
    page_title = _("Update Aggregate Metadata")

    def get_initial(self):
        aggregate = self.get_object()
        return {'id': self.kwargs["id"], 'metadata': aggregate.metadata}

    def get_context_data(self, **kwargs):
        context = super(UpdateMetadataView, self).get_context_data(**kwargs)

        aggregate = self.get_object()
        context['existing_metadata'] = json.dumps(aggregate.metadata)

        resource_type = 'OS::Nova::Aggregate'
        namespaces = []
        try:
            # metadefs_namespace_list() returns a tuple with list as 1st elem
            namespaces = [
                api.glance.metadefs_namespace_get(self.request, x.namespace,
                                                  resource_type)
                for x in api.glance.metadefs_namespace_list(
                    self.request,
                    filters={'resource_types': [resource_type]}
                )[0]
            ]

        except Exception:
            msg = _('Unable to retrieve available metadata for aggregate.')
            exceptions.handle(self.request, msg)

        context['available_metadata'] = json.dumps({'namespaces': namespaces})
        context['id'] = self.kwargs['id']
        return context

    @memoized.memoized_method
    def get_object(self):
        aggregate_id = self.kwargs['id']
        try:
            return api.nova.aggregate_get(self.request, aggregate_id)
        except Exception:
            msg = _('Unable to retrieve the aggregate to be '
                    'updated.')
            exceptions.handle(
                self.request, msg, redirect=reverse(INDEX_URL))


class ManageHostsView(workflows.WorkflowView):
    template_name = constants.AGGREGATES_MANAGE_HOSTS_TEMPLATE
    workflow_class = aggregate_workflows.ManageAggregateHostsWorkflow
    success_url = reverse_lazy(constants.AGGREGATES_INDEX_URL)
    page_title = _("Manage Hosts Aggregate")

    def get_initial(self):
        return {'id': self.kwargs["id"]}

    def get_context_data(self, **kwargs):
        context = super(ManageHostsView, self).get_context_data(**kwargs)
        context['id'] = self.kwargs['id']
        return context
