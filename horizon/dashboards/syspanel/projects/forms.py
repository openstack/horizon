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

from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import exceptions
from horizon import forms
from horizon import messages


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
            messages.success(request, _('Successfully added user to project.'))
            return True
        except:
            exceptions.handle(request, _('Unable to add user to project.'))


class CreateTenant(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"))
    description = forms.CharField(
            widget=forms.widgets.Textarea(),
            label=_("Description"),
            required=False)
    enabled = forms.BooleanField(label=_("Enabled"), required=False,
            initial=True)

    def handle(self, request, data):
        try:
            LOG.info('Creating project with name "%s"' % data['name'])
            project = api.tenant_create(request,
                                        data['name'],
                                        data['description'],
                                        data['enabled'])
            messages.success(request,
                             _('%s was successfully created.')
                             % data['name'])
            return project
        except:
            exceptions.handle(request, _('Unable to create project.'))


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
            LOG.info('Updating project with id "%s"' % data['id'])
            project = api.tenant_update(request,
                                        data['id'],
                                        data['name'],
                                        data['description'],
                                        data['enabled'])
            messages.success(request,
                             _('%s was successfully updated.')
                             % data['name'])
            return project
        except:
            exceptions.handle(request, _('Unable to update project.'))


class UpdateQuotas(forms.SelfHandlingForm):
    tenant_id = forms.CharField(label=_("ID (name)"),
            widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    metadata_items = forms.IntegerField(label=_("Metadata Items"))
    injected_files = forms.IntegerField(label=_("Injected Files"))
    injected_file_content_bytes = forms.IntegerField(label=_("Injected File "
                                                          "Content Bytes"))
    cores = forms.IntegerField(label=_("VCPUs"))
    instances = forms.IntegerField(label=_("Instances"))
    volumes = forms.IntegerField(label=_("Volumes"))
    gigabytes = forms.IntegerField(label=_("Gigabytes"))
    ram = forms.IntegerField(label=_("RAM (in MB)"))
    floating_ips = forms.IntegerField(label=_("Floating IPs"))

    def handle(self, request, data):
        ifcb = data['injected_file_content_bytes']
        try:
            api.nova.tenant_quota_update(request,
                                         data['tenant_id'],
                                         metadata_items=data['metadata_items'],
                                         injected_file_content_bytes=ifcb,
                                         volumes=data['volumes'],
                                         gigabytes=data['gigabytes'],
                                         ram=data['ram'],
                                         floating_ips=data['floating_ips'],
                                         instances=data['instances'],
                                         injected_files=data['injected_files'],
                                         cores=data['cores'])
            messages.success(request,
                             _('Quotas for %s were successfully updated.')
                             % data['tenant_id'])
            return True
        except:
            exceptions.handle(request, _('Unable to update quotas.'))
