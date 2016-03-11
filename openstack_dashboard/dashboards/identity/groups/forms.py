# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


LOG = logging.getLogger(__name__)


class CreateGroupForm(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"))
    description = forms.CharField(widget=forms.widgets.Textarea(
                                  attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)

    def handle(self, request, data):
        try:
            LOG.info('Creating group with name "%s"' % data['name'])
            domain_context = api.keystone.get_effective_domain_id(request)
            api.keystone.group_create(
                request,
                domain_id=domain_context,
                name=data['name'],
                description=data['description'])
            messages.success(request,
                             _('Group "%s" was successfully created.')
                             % data['name'])
        except Exception:
            exceptions.handle(request, _('Unable to create group.'))
            return False
        return True


class UpdateGroupForm(forms.SelfHandlingForm):
    group_id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(label=_("Name"))
    description = forms.CharField(widget=forms.widgets.Textarea(
                                  attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)

    def handle(self, request, data):
        group_id = data.pop('group_id')

        try:
            api.keystone.group_update(request,
                                      group_id=group_id,
                                      name=data['name'],
                                      description=data['description'])
            messages.success(request,
                             _('Group has been updated successfully.'))
        except Exception:
            exceptions.handle(request, _('Unable to update the group.'))
            return False
        return True
