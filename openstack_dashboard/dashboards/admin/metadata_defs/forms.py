#
#    (c) Copyright 2014 Hewlett-Packard Development Company, L.P.
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
Forms for managing metadata.
"""
import json

from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.api import glance
from openstack_dashboard.dashboards.admin.metadata_defs \
    import constants


class CreateNamespaceForm(forms.SelfHandlingForm):
    source_type = forms.ChoiceField(
        label=_('Namespace Definition Source'),
        required=False,
        choices=[('file', _('Metadata Definition File')),
                 ('raw', _('Direct Input'))],
        widget=forms.ThemableSelectWidget(
            attrs={'class': 'switchable', 'data-slug': 'source'}))

    metadef_file = forms.FileField(
        label=_("Metadata Definition File"),
        help_text=_("A local metadata definition file to upload."),
        widget=forms.FileInput(
            attrs={'class': 'switched', 'data-switch-on': 'source',
                   'data-source-file': _('Metadata Definition File')}),
        required=False)

    direct_input = forms.CharField(
        label=_('Namespace JSON'),
        help_text=_('The JSON formatted contents of a namespace.'),
        widget=forms.widgets.Textarea(
            attrs={'class': 'switched', 'data-switch-on': 'source',
                   'data-source-raw': _('Namespace JSON')}),
        required=False)

    public = forms.BooleanField(label=_("Public"), required=False)
    protected = forms.BooleanField(label=_("Protected"), required=False)

    def __init__(self, request, *args, **kwargs):
        super(CreateNamespaceForm, self).__init__(request, *args, **kwargs)

    def clean(self):
        data = super(CreateNamespaceForm, self).clean()

        # The key can be missing based on particular upload
        # conditions. Code defensively for it here...
        metadef_file = data.get('metadef_file', None)
        metadata_raw = data.get('direct_input', None)

        if metadata_raw and metadef_file:
            raise ValidationError(
                _("Cannot specify both file and direct input."))
        if not metadata_raw and not metadef_file:
            raise ValidationError(
                _("No input was provided for the namespace content."))
        try:
            if metadef_file:
                ns_str = self.files['metadef_file'].read()
            else:
                ns_str = data['direct_input']
            namespace = json.loads(ns_str)

            if data['public']:
                namespace['visibility'] = 'public'
            else:
                namespace['visibility'] = 'private'

            namespace['protected'] = data['protected']

            for protected_prop in constants.METADEFS_PROTECTED_PROPS:
                namespace.pop(protected_prop, None)

            data['namespace'] = namespace
        except Exception as e:
            msg = _('There was a problem loading the namespace: %s.') % e
            raise forms.ValidationError(msg)

        return data

    def handle(self, request, data):
        try:
            namespace = glance.metadefs_namespace_create(request,
                                                         data['namespace'])
            messages.success(request,
                             _('Namespace %s has been created.') %
                             namespace['namespace'])
            return namespace
        except Exception as e:
            msg = _('Unable to create new namespace. %s')
            msg %= e.message.split('Failed validating', 1)[0]
            exceptions.handle(request, message=msg)
            return False


class ManageResourceTypesForm(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super(ManageResourceTypesForm, self).__init__(request, *args, **kwargs)

    def handle(self, request, context):
        namespace_name = self.initial['id']
        current_names = self.get_names(self.initial['resource_types'])
        try:
            updated_types = json.loads(self.data['resource_types'])
            selected_types = [updated_type for updated_type in updated_types
                              if updated_type.pop('selected', False)]
            for current_name in current_names:
                glance.metadefs_namespace_remove_resource_type(
                    self.request, namespace_name, current_name)
            for selected_type in selected_types:
                selected_type.pop('$$hashKey', None)
                selected_type.pop('created_at', None)
                selected_type.pop('updated_at', None)
                glance.metadefs_namespace_add_resource_type(
                    self.request, namespace_name, selected_type)
            msg = _('Resource types updated for namespace %s.')
            msg %= namespace_name
            messages.success(request, msg)
        except Exception:
            msg = _('Error updating resource types for namespace %s.')
            msg %= namespace_name
            exceptions.handle(request, msg)
            return False
        return True

    def get_names(self, items):
        return [item['name'] for item in items]


class UpdateNamespaceForm(forms.SelfHandlingForm):

    public = forms.BooleanField(label=_("Public"), required=False)
    protected = forms.BooleanField(label=_("Protected"), required=False)

    def __init__(self, request, *args, **kwargs):
        super(UpdateNamespaceForm, self).__init__(request, *args, **kwargs)

    def handle(self, request, data):
        try:
            params = {
                'visibility': 'public' if data['public'] else 'private',
                'protected': data['protected']
            }
            glance.metadefs_namespace_update(request,
                                             self.initial['namespace_id'],
                                             **params)
            msg = _('Namespace successfully updated.')
            messages.success(request, msg)
        except Exception:
            msg = _('Error updating attributes for namespace.')
            redirect = reverse(constants.METADATA_INDEX_URL)
            exceptions.handle(request, msg, redirect=redirect)
            return False
        return True
