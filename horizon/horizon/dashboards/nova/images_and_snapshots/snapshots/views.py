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

"""
Views for managing Nova instance snapshots.
"""

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from horizon import api
from horizon import exceptions
from horizon import forms
from .forms import CreateSnapshot


LOG = logging.getLogger(__name__)


class CreateView(forms.ModalFormView):
    form_class = CreateSnapshot
    template_name = 'nova/images_and_snapshots/snapshots/create.html'

    def get_initial(self):
        redirect = reverse('horizon:nova:instances_and_volumes:index')
        instance_id = self.kwargs["instance_id"]
        try:
            self.instance = api.server_get(self.request, instance_id)
        except:
            self.instance = None
            msg = _("Unable to retrieve instance.")
            exceptions.handle(self.request, msg, redirect)
        if self.instance.status != api.nova.INSTANCE_ACTIVE_STATE:
            msg = _('To create a snapshot, the instance must be in '
                    'the "%s" state.') % api.nova.INSTANCE_ACTIVE_STATE
            raise exceptions.Http302(redirect, message=msg)
        return {"instance_id": instance_id,
                "tenant_id": self.request.user.tenant_id}

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['instance'] = self.instance
        return context
