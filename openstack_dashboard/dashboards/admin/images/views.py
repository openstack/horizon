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

import logging

from oslo_utils import units

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import messages
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.images.images import views
from openstack_dashboard import policy

from openstack_dashboard.dashboards.admin.images import forms as project_forms
from openstack_dashboard.dashboards.admin.images \
    import tables as project_tables


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    DEFAULT_FILTERS = {'is_public': None}
    table_class = project_tables.AdminImagesTable
    page_title = _("Images")

    def has_prev_data(self, table):
        return self._prev

    def has_more_data(self, table):
        return self._more

    def needs_filter_first(self, table):
        return self._needs_filter_first

    def get_data(self):
        images = []

        if not policy.check((("image", "get_images"),), self.request):
            msg = _("Insufficient privilege level to retrieve image list.")
            messages.info(self.request, msg)
            return images
        filters = self.get_filters()

        filter_first = getattr(settings, 'FILTER_DATA_FIRST', {})
        if filter_first.get('admin.images', False) and \
                len(filters) == len(self.DEFAULT_FILTERS):
            self._prev = False
            self._more = False
            self._needs_filter_first = True
            return images

        self._needs_filter_first = False

        prev_marker = self.request.GET.get(
            project_tables.AdminImagesTable._meta.prev_pagination_param, None)

        if prev_marker is not None:
            marker = prev_marker
        else:
            marker = self.request.GET.get(
                project_tables.AdminImagesTable._meta.pagination_param, None)
        reversed_order = prev_marker is not None
        try:
            images, self._more, self._prev = api.glance.image_list_detailed(
                self.request,
                marker=marker,
                paginate=True,
                filters=filters,
                sort_dir='asc',
                sort_key='name',
                reversed_order=reversed_order)

        except Exception:
            self._prev = False
            self._more = False
            msg = _('Unable to retrieve image list.')
            exceptions.handle(self.request, msg)
        if images:
            try:
                tenants, more = api.keystone.tenant_list(self.request)
            except Exception:
                tenants = []
                msg = _('Unable to retrieve project list.')
                exceptions.handle(self.request, msg)

            tenant_dict = dict([(t.id, t.name) for t in tenants])

            for image in images:
                image.tenant_name = tenant_dict.get(image.owner)
        return images

    def get_filters(self):
        filters = self.DEFAULT_FILTERS.copy()
        filter_field = self.table.get_filter_field()
        filter_string = self.table.get_filter_string()
        filter_action = self.table._meta._filter_action
        if filter_field and filter_string and (
                filter_action.is_api_filter(filter_field)):
            if filter_field in ['size_min', 'size_max']:
                invalid_msg = ('API query is not valid and is ignored: '
                               '%(field)s=%(string)s')
                try:
                    filter_string = long(float(filter_string) * (units.Mi))
                    if filter_string >= 0:
                        filters[filter_field] = filter_string
                    else:
                        LOG.warning(invalid_msg,
                                    {'field': filter_field,
                                     'string': filter_string})
                except ValueError:
                    LOG.warning(invalid_msg,
                                {'field': filter_field,
                                 'string': filter_string})
            elif (filter_field == 'disk_format' and
                  filter_string.lower() == 'docker'):
                filters['disk_format'] = 'raw'
                filters['container_format'] = 'docker'
            else:
                filters[filter_field] = filter_string
        return filters


class CreateView(views.CreateView):
    template_name = 'admin/images/create.html'
    form_class = project_forms.AdminCreateImageForm
    submit_url = reverse_lazy('horizon:admin:images:create')
    success_url = reverse_lazy('horizon:admin:images:index')
    page_title = _("Create An Image")


class UpdateView(views.UpdateView):
    template_name = 'admin/images/update.html'
    form_class = project_forms.AdminUpdateImageForm
    submit_url = "horizon:admin:images:update"
    success_url = reverse_lazy('horizon:admin:images:index')
    page_title = _("Edit Image")


class DetailView(views.DetailView):

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        table = project_tables.AdminImagesTable(self.request)
        context["url"] = reverse('horizon:admin:images:index')
        context["actions"] = table.render_row_actions(context["image"])
        return context
