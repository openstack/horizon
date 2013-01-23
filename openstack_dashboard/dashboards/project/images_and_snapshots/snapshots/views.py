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

"""
Views for managing instance snapshots.
"""

import logging

from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms

from openstack_dashboard import api
from .forms import CreateSnapshot


LOG = logging.getLogger(__name__)


class CreateView(forms.ModalFormView):
    form_class = CreateSnapshot
    template_name = 'project/images_and_snapshots/snapshots/create.html'
    success_url = reverse_lazy("horizon:project:images_and_snapshots:index")

    def get_object(self):
        if not hasattr(self, "_object"):
            try:
                self._object = api.nova.server_get(self.request,
                                                   self.kwargs["instance_id"])
            except:
                redirect = reverse('horizon:project:instances:index')
                exceptions.handle(self.request,
                                  _("Unable to retrieve instance."),
                                  redirect=redirect)
        return self._object

    def get_initial(self):
        return {"instance_id": self.kwargs["instance_id"]}

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['instance'] = self.get_object()
        return context
