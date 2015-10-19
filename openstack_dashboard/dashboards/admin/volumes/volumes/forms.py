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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import validators as utils_validators

from openstack_dashboard.api import cinder
from openstack_dashboard.dashboards.admin.volumes.snapshots.forms \
    import populate_status_choices
from openstack_dashboard.dashboards.project.volumes.volumes \
    import forms as project_forms


# This set of states was pulled from cinder's admin_actions.py
STATUS_CHOICES = (
    ('attaching', _('Attaching')),
    ('available', _('Available')),
    ('creating', _('Creating')),
    ('deleting', _('Deleting')),
    ('detaching', _('Detaching')),
    ('error', _('Error')),
    ('error_deleting', _('Error Deleting')),
    ('in-use', _('In Use')),
    ('maintenance', _('Maintenance')),
)


class ManageVolume(forms.SelfHandlingForm):
    identifier = forms.CharField(
        max_length=255,
        label=_("Identifier"),
        help_text=_("Name or other identifier for existing volume"))
    id_type = forms.ChoiceField(
        label=_("Identifier Type"),
        help_text=_("Type of backend device identifier provided"))
    host = forms.CharField(
        max_length=255,
        label=_("Host"),
        help_text=_("Cinder host on which the existing volume resides; "
                    "takes the form: host@backend-name#pool"))
    name = forms.CharField(
        max_length=255,
        label=_("Volume Name"),
        required=False,
        help_text=_("Volume name to be assigned"))
    description = forms.CharField(max_length=255, widget=forms.Textarea(
        attrs={'rows': 4}),
        label=_("Description"), required=False)
    metadata = forms.CharField(max_length=255, widget=forms.Textarea(
        attrs={'rows': 2}),
        label=_("Metadata"), required=False,
        help_text=_("Comma-separated key=value pairs"),
        validators=[utils_validators.validate_metadata])
    volume_type = forms.ChoiceField(
        label=_("Volume Type"),
        required=False)
    availability_zone = forms.ChoiceField(
        label=_("Availability Zone"),
        required=False)

    bootable = forms.BooleanField(
        label=_("Bootable"),
        required=False,
        help_text=_("Specifies that the newly created volume "
                    "should be marked as bootable"))

    def __init__(self, request, *args, **kwargs):
        super(ManageVolume, self).__init__(request, *args, **kwargs)
        self.fields['id_type'].choices = [("source-name", _("Name"))] + \
                                         [("source-id", _("ID"))]
        volume_types = cinder.volume_type_list(request)
        self.fields['volume_type'].choices = [("", _("No volume type"))] + \
                                             [(type.name, type.name)
                                              for type in volume_types]
        self.fields['availability_zone'].choices = \
            project_forms.availability_zones(request)

    def handle(self, request, data):
        try:
            az = data.get('availability_zone')

            # assume user enters metadata with "key1=val1,key2=val2"
            # convert to dictionary
            metadataDict = {}
            metadata = data.get('metadata')
            if metadata:
                metadata.replace(" ", "")
                for item in metadata.split(','):
                    key, value = item.split('=')
                    metadataDict[key] = value

            cinder.volume_manage(request,
                                 host=data['host'],
                                 identifier=data['identifier'],
                                 id_type=data['id_type'],
                                 name=data['name'],
                                 description=data['description'],
                                 volume_type=data['volume_type'],
                                 availability_zone=az,
                                 metadata=metadataDict,
                                 bootable=data['bootable'])

            # for success message, use identifier if user does not
            # provide a volume name
            volume_name = data['name']
            if not volume_name:
                volume_name = data['identifier']

            messages.success(
                request,
                _('Successfully sent the request to manage volume: %s')
                % volume_name)
            return True
        except Exception:
            redirect = reverse("horizon:admin:volumes:index")
            exceptions.handle(request, _("Unable to manage volume."),
                              redirect=redirect)


class UnmanageVolume(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Volume Name"),
                           required=False,
                           widget=forms.TextInput(
                           attrs={'readonly': 'readonly'}))
    host = forms.CharField(label=_("Host"),
                           required=False,
                           widget=forms.TextInput(
                           attrs={'readonly': 'readonly'}))
    volume_id = forms.CharField(label=_("ID"),
                                required=False,
                                widget=forms.TextInput(
                                    attrs={'readonly': 'readonly'}))

    def handle(self, request, data):
        try:
            cinder.volume_unmanage(request, self.initial['volume_id'])
            messages.success(
                request,
                _('Successfully sent the request to unmanage volume: %s')
                % data['name'])
            return True
        except Exception:
            redirect = reverse("horizon:admin:volumes:index")
            exceptions.handle(request, _("Unable to unmanage volume."),
                              redirect=redirect)


class MigrateVolume(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Volume Name"),
                           required=False,
                           widget=forms.TextInput(
                           attrs={'readonly': 'readonly'}))
    current_host = forms.CharField(label=_("Current Host"),
                                   required=False,
                                   widget=forms.TextInput(
                                   attrs={'readonly': 'readonly'}))
    host = forms.ChoiceField(label=_("Destination Host"),
                             help_text=_("Choose a Host to migrate to."))
    force_host_copy = forms.BooleanField(label=_("Force Host Copy"),
                                         initial=False, required=False)

    def __init__(self, request, *args, **kwargs):
        super(MigrateVolume, self).__init__(request, *args, **kwargs)
        initial = kwargs.get('initial', {})
        self.fields['host'].choices = self.populate_host_choices(request,
                                                                 initial)

    def populate_host_choices(self, request, initial):
        hosts = initial.get('hosts')
        current_host = initial.get('current_host')
        host_list = [(host.name, host.name)
                     for host in hosts
                     if host.name != current_host]
        if host_list:
            host_list.insert(0, ("", _("Select a new host")))
        else:
            host_list.insert(0, ("", _("No other hosts available")))
        return sorted(host_list)

    def handle(self, request, data):
        try:
            cinder.volume_migrate(request,
                                  self.initial['volume_id'],
                                  data['host'],
                                  data['force_host_copy'])
            messages.success(
                request,
                _('Successfully sent the request to migrate volume: %s')
                % data['name'])
            return True
        except Exception:
            redirect = reverse("horizon:admin:volumes:volumes_tab")
            exceptions.handle(request, _("Failed to migrate volume."),
                              redirect=redirect)


class UpdateStatus(forms.SelfHandlingForm):
    status = forms.ChoiceField(label=_("Status"))

    def __init__(self, request, *args, **kwargs):
        super(UpdateStatus, self).__init__(request, *args, **kwargs)

        initial = kwargs.get('initial', {})
        self.fields['status'].choices = (
            populate_status_choices(initial, STATUS_CHOICES))

    def handle(self, request, data):
        # Obtain the localized status for including in the message
        for choice in self.fields['status'].choices:
            if choice[0] == data['status']:
                new_status = choice[1]
                break
        else:
            new_status = data['status']

        try:
            cinder.volume_reset_state(request,
                                      self.initial['volume_id'],
                                      data['status'])
            messages.success(request,
                             _('Successfully updated volume status to "%s".') %
                             new_status)
            return True
        except Exception:
            redirect = reverse("horizon:admin:volumes:index")
            exceptions.handle(request,
                              _('Unable to update volume status to "%s".') %
                              new_status, redirect=redirect)
