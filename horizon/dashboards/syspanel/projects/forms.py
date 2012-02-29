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

from django import shortcuts
from django.contrib import messages
from django.utils.translation import ugettext as _

from horizon import api
from horizon import exceptions
from horizon import forms


LOG = logging.getLogger(__name__)


class AddUser(forms.SelfHandlingForm):
    tenant_id = forms.CharField(widget=forms.widgets.HiddenInput())
    user_id = forms.CharField(widget=forms.widgets.HiddenInput())
    role_id = forms.ChoiceField(label=_("Role"))

    def __init__(self, *args, **kwargs):
        roles = kwargs.pop('roles')
        super(AddUser, self).__init__(*args, **kwargs)
        role_choices = [(role.id, role.name) for role in roles]
        self.fields['role_id'].choices = role_choices

    def handle(self, request, data):
        try:
            api.add_tenant_user_role(request,
                                     data['tenant_id'],
                                     data['user_id'],
                                     data['role_id'])
            messages.success(request, _('Successfully added user to tenant.'))
        except:
            exceptions.handle(request, _('Unable to add user to tenant.'))
        return shortcuts.redirect('horizon:syspanel:projects:users',
                                  tenant_id=data['tenant_id'])


class CreateTenant(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"))
    description = forms.CharField(
            widget=forms.widgets.Textarea(),
            label=_("Description"))
    enabled = forms.BooleanField(label=_("Enabled"), required=False,
            initial=True)

    def handle(self, request, data):
        try:
            LOG.info('Creating tenant with name "%s"' % data['name'])
            api.tenant_create(request,
                              data['name'],
                              data['description'],
                              data['enabled'])
            messages.success(request,
                             _('%s was successfully created.')
                             % data['name'])
        except:
            exceptions.handle(request, _('Unable to create tenant.'))
        return shortcuts.redirect('horizon:syspanel:projects:index')


class UpdateTenant(forms.SelfHandlingForm):
    id = forms.CharField(label=_("ID"),
            widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    name = forms.CharField(label=_("Name"))
    description = forms.CharField(
            widget=forms.widgets.Textarea(),
            label=_("Description"))
    enabled = forms.BooleanField(required=False, label=_("Enabled"))

    def handle(self, request, data):
        try:
            LOG.info('Updating tenant with id "%s"' % data['id'])
            api.tenant_update(request,
                              data['id'],
                              data['name'],
                              data['description'],
                              data['enabled'])
            messages.success(request,
                             _('%s was successfully updated.')
                             % data['name'])
        except:
            exceptions.handle(request, _('Unable to update tenant.'))
        return shortcuts.redirect('horizon:syspanel:projects:index')


class UpdateQuotas(forms.SelfHandlingForm):
    tenant_id = forms.CharField(label=_("ID (name)"),
            widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    metadata_items = forms.CharField(label=_("Metadata Items"))
    injected_files = forms.CharField(label=_("Injected Files"))
    injected_file_content_bytes = forms.CharField(label=_("Injected File "
                                                          "Content Bytes"))
    cores = forms.CharField(label=_("VCPUs"))
    instances = forms.CharField(label=_("Instances"))
    volumes = forms.CharField(label=_("Volumes"))
    gigabytes = forms.CharField(label=_("Gigabytes"))
    ram = forms.CharField(label=_("RAM (in MB)"))
    floating_ips = forms.CharField(label=_("Floating IPs"))

    def handle(self, request, data):
        try:
            api.nova.tenant_quota_update(request,
               data['tenant_id'],
               metadata_items=data['metadata_items'],
               injected_file_content_bytes=data['injected_file_content_bytes'],
               volumes=data['volumes'],
               gigabytes=data['gigabytes'],
               ram=int(data['ram']),
               floating_ips=data['floating_ips'],
               instances=data['instances'],
               injected_files=data['injected_files'],
               cores=data['cores'],
            )
            messages.success(request,
                             _('Quotas for %s were successfully updated.')
                             % data['tenant_id'])
        except:
            exceptions.handle(request, _('Unable to update quotas.'))
        return shortcuts.redirect('horizon:syspanel:projects:index')
