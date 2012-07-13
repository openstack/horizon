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

from horizon import api
from horizon import exceptions
from horizon import forms
from horizon import tables
from .forms import CreateFlavor
from .tables import FlavorsTable


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = FlavorsTable
    template_name = 'syspanel/flavors/index.html'

    def get_data(self):
        request = self.request
        flavors = []
        try:
            flavors = api.flavor_list(request)
        except:
            exceptions.handle(request,
                              _('Unable to retrieve flavor list.'))
        flavors.sort(key=lambda x: x.id, reverse=True)
        return flavors


class CreateView(forms.ModalFormView):
    form_class = CreateFlavor
    template_name = 'syspanel/flavors/create.html'
    success_url = reverse_lazy('horizon:syspanel:flavors:index')

    def get_initial(self):
        # TODO(tres): Get rid of this hacky bit of nonsense after flavors
        # id handling gets fixed.
        try:
            flavors = api.flavor_list(self.request)
        except:
            exceptions.handle(self.request, ignore=True)
        if flavors:
            largest_id = max(flavors, key=lambda f: f.id).id
            return {'flavor_id': int(largest_id) + 1}
        else:
            return {'flavor_id': 1}
