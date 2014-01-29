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
from django.utils import http
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.images.properties \
    import forms as project_forms
from openstack_dashboard.dashboards.admin.images.properties \
    import tables as project_tables


class PropertyMixin(object):
    def get_context_data(self, **kwargs):
        context = super(PropertyMixin, self).get_context_data(**kwargs)
        try:
            context['image'] = api.glance.image_get(self.request,
                                                    self.kwargs['id'])
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve image details."))
        if 'key' in self.kwargs:
            context['encoded_key'] = self.kwargs['key']
            context['key'] = http.urlunquote(self.kwargs['key'])
        return context

    def get_success_url(self):
        return reverse("horizon:admin:images:properties:index",
                       args=(self.kwargs["id"],))


class IndexView(PropertyMixin, tables.DataTableView):
    table_class = project_tables.PropertiesTable
    template_name = 'admin/images/properties/index.html'

    def get_data(self):
        try:
            image_id = self.kwargs['id']
            properties_list = api.glance.image_get_properties(self.request,
                                                              image_id,
                                                              False)
            properties_list.sort(key=lambda prop: (prop.key,))
        except Exception:
            properties_list = []
            exceptions.handle(self.request,
                        _('Unable to retrieve image custom properties list.'))
        return properties_list


class CreateView(PropertyMixin, forms.ModalFormView):
    form_class = project_forms.CreateProperty
    template_name = 'admin/images/properties/create.html'

    def get_initial(self):
        return {'image_id': self.kwargs['id']}


class EditView(PropertyMixin, forms.ModalFormView):
    form_class = project_forms.EditProperty
    template_name = 'admin/images/properties/edit.html'

    def get_initial(self):
        image_id = self.kwargs['id']
        key = http.urlunquote(self.kwargs['key'])
        try:
            prop = api.glance.image_get_property(self.request, image_id,
                                                 key, False)
        except Exception:
            prop = None
            exceptions.handle(self.request,
                              _('Unable to retrieve image custom property.'))
        return {'image_id': image_id,
                'key': key,
                'value': prop.value if prop else ''}
