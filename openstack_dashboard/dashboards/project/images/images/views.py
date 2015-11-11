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

"""
Views for managing images.
"""
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.utils import filters

from openstack_dashboard.dashboards.project.images.images \
    import forms as project_forms
from openstack_dashboard.dashboards.project.images.images \
    import tables as project_tables
from openstack_dashboard.dashboards.project.images.images \
    import tabs as project_tabs


class CreateView(forms.ModalFormView):
    form_class = project_forms.CreateImageForm
    form_id = "create_image_form"
    modal_header = _("Create An Image")
    submit_label = _("Create Image")
    submit_url = reverse_lazy('horizon:project:images:images:create')
    template_name = 'project/images/images/create.html'
    context_object_name = 'image'
    success_url = reverse_lazy("horizon:project:images:index")
    page_title = _("Create An Image")

    def get_initial(self):
        initial = {}
        for name in [
            'name',
            'description',
            'image_url',
            'source_type',
            'architecture',
            'disk_format',
            'minimum_disk',
            'minimum_ram'
        ]:
            tmp = self.request.GET.get(name)
            if tmp:
                initial[name] = tmp
        return initial


class UpdateView(forms.ModalFormView):
    form_class = project_forms.UpdateImageForm
    form_id = "update_image_form"
    modal_header = _("Update Image")
    submit_label = _("Update Image")
    submit_url = "horizon:project:images:images:update"
    template_name = 'project/images/images/update.html'
    success_url = reverse_lazy("horizon:project:images:index")
    page_title = _("Update Image")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.glance.image_get(self.request, self.kwargs['image_id'])
        except Exception:
            msg = _('Unable to retrieve image.')
            url = reverse('horizon:project:images:index')
            exceptions.handle(self.request, msg, redirect=url)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['image'] = self.get_object()
        args = (self.kwargs['image_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        image = self.get_object()
        properties = getattr(image, 'properties', {})
        data = {'image_id': self.kwargs['image_id'],
                'name': getattr(image, 'name', None) or image.id,
                'description': properties.get('description', ''),
                'kernel': properties.get('kernel_id', ''),
                'ramdisk': properties.get('ramdisk_id', ''),
                'architecture': properties.get('architecture', ''),
                'minimum_ram': getattr(image, 'min_ram', None),
                'minimum_disk': getattr(image, 'min_disk', None),
                'public': getattr(image, 'is_public', None),
                'protected': getattr(image, 'protected', None)}
        disk_format = getattr(image, 'disk_format', None)
        if (disk_format == 'raw' and
                getattr(image, 'container_format') == 'docker'):
            disk_format = 'docker'
        data['disk_format'] = disk_format
        return data


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.ImageDetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ image.name }}"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        image = self.get_data()
        table = project_tables.ImagesTable(self.request)
        context["image"] = image
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(image)
        choices = project_tables.ImagesTable.STATUS_DISPLAY_CHOICES
        image.status_label = filters.get_display_label(choices, image.status)
        return context

    @staticmethod
    def get_redirect_url():
        return reverse_lazy('horizon:project:images:index')

    @memoized.memoized_method
    def get_data(self):
        try:
            return api.glance.image_get(self.request, self.kwargs['image_id'])
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve image details.'),
                              redirect=self.get_redirect_url())

    def get_tabs(self, request, *args, **kwargs):
        image = self.get_data()
        return self.tab_group_class(request, image=image, **kwargs)
