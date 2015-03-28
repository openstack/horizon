# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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
import logging

from oslo_utils import units

from django import conf
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.images.images import views

from openstack_dashboard.dashboards.admin.images import forms as project_forms
from openstack_dashboard.dashboards.admin.images \
    import tables as project_tables

LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = project_tables.AdminImagesTable
    template_name = 'admin/images/index.html'
    page_title = _("Images")

    def has_prev_data(self, table):
        return self._prev

    def has_more_data(self, table):
        return self._more

    def get_data(self):
        images = []
        filters = self.get_filters()
        prev_marker = self.request.GET.get(
            project_tables.AdminImagesTable._meta.prev_pagination_param, None)

        if prev_marker is not None:
            sort_dir = 'asc'
            marker = prev_marker
        else:
            sort_dir = 'desc'
            marker = self.request.GET.get(
                project_tables.AdminImagesTable._meta.pagination_param, None)
        try:
            images, self._more, self._prev = api.glance.image_list_detailed(
                self.request,
                marker=marker,
                paginate=True,
                filters=filters,
                sort_dir=sort_dir)

            if prev_marker is not None:
                images = sorted(images, key=lambda image:
                                getattr(image, 'created_at'), reverse=True)

        except Exception:
            self._prev = False
            self._more = False
            msg = _('Unable to retrieve image list.')
            exceptions.handle(self.request, msg)
        return images

    def get_filters(self):
        filters = {'is_public': None}
        filter_field = self.table.get_filter_field()
        filter_string = self.table.get_filter_string()
        filter_action = self.table._meta._filter_action
        if filter_field and filter_string and (
                filter_action.is_api_filter(filter_field)):
            if filter_field in ['size_min', 'size_max']:
                invalid_msg = ('API query is not valid and is ignored: %s=%s'
                               % (filter_field, filter_string))
                try:
                    filter_string = long(float(filter_string) * (units.Mi))
                    if filter_string >= 0:
                        filters[filter_field] = filter_string
                    else:
                        LOG.warning(invalid_msg)
                except ValueError:
                    LOG.warning(invalid_msg)
            else:
                filters[filter_field] = filter_string
        return filters


class CreateView(views.CreateView):
    template_name = 'admin/images/create.html'
    form_class = project_forms.AdminCreateImageForm
    success_url = reverse_lazy('horizon:admin:images:index')
    page_title = _("Create An Image")


class UpdateView(views.UpdateView):
    template_name = 'admin/images/update.html'
    form_class = project_forms.AdminUpdateImageForm
    success_url = reverse_lazy('horizon:admin:images:index')
    page_title = _("Update Image")


class DetailView(views.DetailView):

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        table = project_tables.AdminImagesTable(self.request)
        context["url"] = reverse('horizon:admin:images:index')
        context["actions"] = table.render_row_actions(context["image"])
        return context


class UpdateMetadataView(forms.ModalFormView):
    template_name = "admin/images/update_metadata.html"
    form_class = project_forms.UpdateMetadataForm
    success_url = reverse_lazy('horizon:admin:images:index')
    page_title = _("Update Image Metadata")

    def get_initial(self):
        image = self.get_object()
        return {'id': self.kwargs["id"], 'metadata': image.properties}

    def get_context_data(self, **kwargs):
        context = super(UpdateMetadataView, self).get_context_data(**kwargs)

        image = self.get_object()
        reserved_props = getattr(conf.settings,
                                 'IMAGE_RESERVED_CUSTOM_PROPERTIES', [])
        image.properties = dict((k, v)
                                for (k, v) in image.properties.iteritems()
                                if k not in reserved_props)
        context['existing_metadata'] = json.dumps(image.properties)

        resource_type = 'OS::Glance::Image'
        namespaces = []
        try:
            # metadefs_namespace_list() returns a tuple with list as 1st elem
            available_namespaces = [x.namespace for x in
                                    api.glance.metadefs_namespace_list(
                                        self.request,
                                        filters={"resource_types":
                                                 [resource_type]}
                                    )[0]]
            for namespace in available_namespaces:
                details = api.glance.metadefs_namespace_get(self.request,
                                                            namespace,
                                                            resource_type)
                # Filter out reserved custom properties from namespace
                if reserved_props:
                    if hasattr(details, 'properties'):
                        details.properties = dict(
                            (k, v)
                            for (k, v) in details.properties.iteritems()
                            if k not in reserved_props
                        )

                    if hasattr(details, 'objects'):
                        for obj in details.objects:
                            obj['properties'] = dict(
                                (k, v)
                                for (k, v) in obj['properties'].iteritems()
                                if k not in reserved_props
                            )

                namespaces.append(details)

        except Exception:
            msg = _('Unable to retrieve available properties for image.')
            exceptions.handle(self.request, msg)

        context['available_metadata'] = json.dumps({'namespaces': namespaces})
        context['id'] = self.kwargs['id']
        return context

    @memoized.memoized_method
    def get_object(self):
        image_id = self.kwargs['id']
        try:
            return api.glance.image_get(self.request, image_id)
        except Exception:
            msg = _('Unable to retrieve the image to be updated.')
            exceptions.handle(self.request, msg,
                              redirect=reverse('horizon:admin:images:index'))
