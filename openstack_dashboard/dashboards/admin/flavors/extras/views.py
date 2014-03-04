# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright (c) 2012 Intel, Inc.
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
from horizon import forms
from horizon import tables

from openstack_dashboard import api

from openstack_dashboard.dashboards.admin.flavors.extras \
    import forms as project_forms
from openstack_dashboard.dashboards.admin.flavors.extras \
    import tables as project_tables


class ExtraSpecMixin(object):
    def get_context_data(self, **kwargs):
        context = super(ExtraSpecMixin, self).get_context_data(**kwargs)
        try:
            context['flavor'] = api.nova.flavor_get(self.request,
                                                    self.kwargs['id'])
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve flavor details."))
        if 'key' in self.kwargs:
            context['key'] = self.kwargs['key']
        return context


class IndexView(ExtraSpecMixin, forms.ModalFormMixin, tables.DataTableView):
    table_class = project_tables.ExtraSpecsTable
    template_name = 'admin/flavors/extras/index.html'

    def get_data(self):
        try:
            flavor_id = self.kwargs['id']
            extras_list = api.nova.flavor_get_extras(self.request, flavor_id)
            extras_list.sort(key=lambda es: (es.key,))
        except Exception:
            extras_list = []
            exceptions.handle(self.request,
                              _('Unable to retrieve extra spec list.'))
        return extras_list


class CreateView(ExtraSpecMixin, forms.ModalFormView):
    form_class = project_forms.CreateExtraSpec
    template_name = 'admin/flavors/extras/create.html'

    def get_initial(self):
        return {'flavor_id': self.kwargs['id']}

    def get_success_url(self):
        return reverse("horizon:admin:flavors:extras:index",
                       args=(self.kwargs["id"],))


class EditView(ExtraSpecMixin, forms.ModalFormView):
    form_class = project_forms.EditExtraSpec
    template_name = 'admin/flavors/extras/edit.html'
    success_url = 'horizon:admin:flavors:extras:index'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['id'],))

    def get_initial(self):
        flavor_id = self.kwargs['id']
        key = self.kwargs['key']
        try:
            extra_specs = api.nova.flavor_get_extras(self.request,
                                                     flavor_id,
                                                     raw=True)
        except Exception:
            extra_specs = {}
            exceptions.handle(self.request,
                              _('Unable to retrieve flavor extra spec '
                                'details.'))
        return {'flavor_id': flavor_id,
                'key': key,
                'value': extra_specs.get(key, '')}
