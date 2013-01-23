# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables

from openstack_dashboard import api
from .forms import CreateFlavor, EditFlavor
from .tables import FlavorsTable


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = FlavorsTable
    template_name = 'admin/flavors/index.html'

    def get_data(self):
        request = self.request
        flavors = []
        try:
            flavors = api.nova.flavor_list(request)
        except:
            exceptions.handle(request,
                              _('Unable to retrieve flavor list.'))
        # Sort flavors by size
        flavors.sort(key=lambda f: (f.vcpus, f.ram, f.disk))
        return flavors


class CreateView(forms.ModalFormView):
    form_class = CreateFlavor
    template_name = 'admin/flavors/create.html'
    success_url = reverse_lazy('horizon:admin:flavors:index')


class EditView(forms.ModalFormView):
    form_class = EditFlavor
    template_name = 'admin/flavors/edit.html'
    success_url = reverse_lazy('horizon:admin:flavors:index')

    def get_context_data(self, **kwargs):
        context = super(EditView, self).get_context_data(**kwargs)
        context['flavor_id'] = self.kwargs['id']
        return context

    def get_initial(self):
        try:
            flavor = api.nova.flavor_get(self.request, self.kwargs['id'])
        except:
            exceptions.handle(self.request,
                              _("Unable to retrieve flavor data."))
        return {'flavor_id': flavor.id,
                'name': flavor.name,
                'vcpus': flavor.vcpus,
                'memory_mb': flavor.ram,
                'disk_gb': flavor.disk,
                'swap_mb': flavor.swap or 0,
                'eph_gb': getattr(flavor, 'OS-FLV-EXT-DATA:ephemeral', None)}
