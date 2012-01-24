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

from django import shortcuts
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.translation import ugettext as _

from horizon import api
from horizon import exceptions
from horizon import forms


LOG = logging.getLogger(__name__)


class CreateSnapshot(forms.SelfHandlingForm):
    tenant_id = forms.CharField(widget=forms.HiddenInput())
    instance_id = forms.CharField(widget=forms.TextInput(
                                  attrs={'readonly': 'readonly'}))
    name = forms.CharField(max_length="20", label=_("Snapshot Name"))

    def handle(self, request, data):
        try:
            api.snapshot_create(request, data['instance_id'], data['name'])
            # NOTE(gabriel): This API call is only to display a pretty name.
            instance = api.server_get(request, data['instance_id'])
            vals = {"name": data['name'], "inst": instance.name}
            messages.success(request, _('Snapshot "%(name)s" created for '
                                        'instance "%(inst)s"') % vals)
            return shortcuts.redirect('horizon:nova:images_and_snapshots:'
                                      'index')
        except:
            redirect = reverse("horizon:nova:instances_and_volumes:index")
            exceptions.handle(request,
                              _('Unable to create snapshot.'),
                              redirect=redirect)
