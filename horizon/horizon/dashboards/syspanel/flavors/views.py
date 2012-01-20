# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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

from django.contrib import messages
from django.utils.translation import ugettext as _
from novaclient import exceptions as api_exceptions

from horizon import api
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
        except api_exceptions.Unauthorized, e:
            LOG.exception('Unauthorized attempt to access flavor list.')
            messages.error(request, _('Unauthorized.'))
        except Exception, e:
            LOG.exception('Exception while fetching usage info')
            if not hasattr(e, 'message'):
                e.message = str(e)
            messages.error(request, _('Unable to get flavor list: %s') %
                           e.message)
        flavors.sort(key=lambda x: x.id, reverse=True)
        return flavors


class CreateView(forms.ModalFormView):
    form_class = CreateFlavor
    template_name = 'syspanel/flavors/create.html'

    def get_initial(self):
        # TODO(tres): Get rid of this hacky bit of nonsense after flavors get
        # converted to nova client.
        flavors = api.flavor_list(self.request)
        flavors.sort(key=lambda f: f.id, reverse=True)
        return {'flavor_id': int(flavors[0].id) + 1}
