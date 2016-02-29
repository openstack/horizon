#    (c) Copyright 2014 Hewlett-Packard Development Company, L.P.
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

import json

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard.api import glance
from openstack_dashboard.dashboards.admin.metadata_defs \
    import constants
from openstack_dashboard.dashboards.admin.metadata_defs \
    import forms as admin_forms
from openstack_dashboard.dashboards.admin.metadata_defs \
    import tables as admin_tables
from openstack_dashboard.dashboards.admin.metadata_defs \
    import tabs as admin_tabs


class AdminIndexView(tables.DataTableView):
    table_class = admin_tables.AdminNamespacesTable
    template_name = constants.METADATA_INDEX_TEMPLATE
    page_title = _("Metadata Definitions")

    def has_prev_data(self, table):
        return self._prev

    def has_more_data(self, table):
        return self._more

    def get_data(self):
        namespaces = []
        prev_marker = self.request.GET.get(
            admin_tables.AdminNamespacesTable._meta.prev_pagination_param,
            None)

        if prev_marker is not None:
            sort_dir = 'desc'
            marker = prev_marker
        else:
            sort_dir = 'asc'
            marker = self.request.GET.get(
                admin_tables.AdminNamespacesTable._meta.pagination_param, None)

        try:
            namespaces, self._more, self._prev =\
                glance.metadefs_namespace_list(self.request,
                                               marker=marker,
                                               paginate=True,
                                               sort_dir=sort_dir)

            if prev_marker is not None:
                namespaces = sorted(namespaces,
                                    key=lambda ns: getattr(ns, 'namespace'),
                                    reverse=True)
        except Exception:
            self._prev = False
            self._more = False
            msg = _('Error getting metadata definitions.')
            exceptions.handle(self.request, msg)
        return namespaces


class CreateView(forms.ModalFormView):
    form_class = admin_forms.CreateNamespaceForm
    template_name = constants.METADATA_CREATE_TEMPLATE
    context_object_name = 'namespace'
    success_url = reverse_lazy(constants.METADATA_INDEX_URL)
    page_title = _("Create a Metadata Namespace")
    submit_label = _("Import Namespace")


class DetailView(tabs.TabView):
    redirect_url = constants.METADATA_INDEX_URL
    tab_group_class = admin_tabs.NamespaceDetailTabs
    template_name = constants.METADATA_DETAIL_TEMPLATE
    page_title = "{{ namespace.namespace }}"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["namespace"] = self.get_data()
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            namespace = glance.metadefs_namespace_get(
                self.request, self.kwargs['namespace_id'], wrap=True)
        except Exception:
            url = reverse_lazy(constants.METADATA_INDEX_URL)
            exceptions.handle(self.request,
                              _('Unable to retrieve namespace details.'),
                              redirect=url)
        else:
            return namespace

    def get_tabs(self, request, *args, **kwargs):
        namespace = self.get_data()
        return self.tab_group_class(request, namespace=namespace, **kwargs)


class ManageResourceTypes(forms.ModalFormView):
    template_name = constants.METADATA_MANAGE_RESOURCES_TEMPLATE
    form_class = admin_forms.ManageResourceTypesForm
    success_url = reverse_lazy(constants.METADATA_INDEX_URL)

    def get_initial(self):
        try:
            resource_types = glance.metadefs_namespace_resource_types(
                self.request, self.kwargs["id"])
        except Exception:
            resource_types = []
            msg = _('Error getting resource type associations.')
            exceptions.handle(self.request, msg)
        return {'id': self.kwargs["id"],
                'resource_types': resource_types}

    def get_context_data(self, **kwargs):
        context = super(ManageResourceTypes, self).get_context_data(**kwargs)

        selected_type_names = [selected_type['name'] for selected_type in
                               context['form'].initial['resource_types']]

        try:
            # Set the basic types that aren't already associated
            result = [unselected_type for unselected_type in
                      glance.metadefs_resource_types_list(self.request)
                      if unselected_type['name'] not in selected_type_names]
        except Exception:
            result = []
            msg = _('Error getting resource type associations.')
            exceptions.handle(self.request, msg)

        # Add the resource types previously associated, includes prefix, etc
        for initial_type in context['form'].initial['resource_types']:
            selected_type = initial_type.copy()
            selected_type['selected'] = True
            result.insert(0, selected_type)

        context['id'] = self.kwargs['id']
        try:
            context["resource_types"] = json.dumps(result)
        except Exception:
            context["resource_types"] = "[]"
            msg = _('Error getting resource type associations.')
            exceptions.handle(self.request, msg)

        return context
