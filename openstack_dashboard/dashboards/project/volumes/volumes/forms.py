# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nebula, Inc.
# All rights reserved.

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
Views for managing volumes.
"""

from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms import ValidationError  # noqa
from django.template.defaultfilters import filesizeformat  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import functions
from horizon.utils.memoized import memoized  # noqa

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.api import glance
from openstack_dashboard.dashboards.project.images import utils
from openstack_dashboard.dashboards.project.instances import tables
from openstack_dashboard.usage import quotas


class CreateForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label=_("Volume Name"))
    description = forms.CharField(widget=forms.Textarea(
        attrs={'class': 'modal-body-fixed-width'}),
        label=_("Description"), required=False)
    type = forms.ChoiceField(label=_("Type"),
                             required=False)
    size = forms.IntegerField(min_value=1, label=_("Size (GB)"))
    volume_source_type = forms.ChoiceField(label=_("Volume Source"),
                                           required=False,
                                           widget=forms.Select(attrs={
                                               'class': 'switchable',
                                               'data-slug': 'source'}))
    snapshot_source = forms.ChoiceField(
        label=_("Use snapshot as a source"),
        widget=forms.SelectWidget(
            attrs={'class': 'snapshot-selector'},
            data_attrs=('size', 'name'),
            transform=lambda x: "%s (%sGB)" % (x.name, x.size)),
        required=False)
    image_source = forms.ChoiceField(
        label=_("Use image as a source"),
        widget=forms.SelectWidget(
            attrs={'class': 'image-selector'},
            data_attrs=('size', 'name', 'min_disk'),
            transform=lambda x: "%s (%s)" % (x.name, filesizeformat(x.bytes))),
        required=False)
    volume_source = forms.ChoiceField(
        label=_("Use a volume as source"),
        widget=forms.SelectWidget(
            attrs={'class': 'image-selector'},
            data_attrs=('size', 'name'),
            transform=lambda x: "%s (%s)" % (x.name,
                filesizeformat(x.size * 1024 * 1024 * 1024))),
        required=False)
    availability_zone = forms.ChoiceField(
        label=_("Availability Zone"),
        required=False,
        widget=forms.Select(
            attrs={'class': 'switched',
                   'data-switch-on': 'source',
                   'data-source-no_source_type': _('Availability Zone'),
                   'data-source-image_source': _('Availability Zone')}))

    def __init__(self, request, *args, **kwargs):
        super(CreateForm, self).__init__(request, *args, **kwargs)
        volume_types = cinder.volume_type_list(request)
        self.fields['type'].choices = [("", "")] + \
                                      [(type.name, type.name)
                                       for type in volume_types]

        if "snapshot_id" in request.GET:
            try:
                snapshot = self.get_snapshot(request,
                                             request.GET["snapshot_id"])
                self.fields['name'].initial = snapshot.name
                self.fields['size'].initial = snapshot.size
                self.fields['snapshot_source'].choices = ((snapshot.id,
                                                           snapshot),)
                try:
                    # Set the volume type from the original volume
                    orig_volume = cinder.volume_get(request,
                                                    snapshot.volume_id)
                    self.fields['type'].initial = orig_volume.volume_type
                except Exception:
                    pass
                self.fields['size'].help_text = _('Volume size must be equal '
                            'to or greater than the snapshot size (%sGB)') \
                            % snapshot.size
                del self.fields['image_source']
                del self.fields['volume_source']
                del self.fields['volume_source_type']
                del self.fields['availability_zone']
            except Exception:
                exceptions.handle(request,
                                  _('Unable to load the specified snapshot.'))
        elif 'image_id' in request.GET:
            self.fields['availability_zone'].choices = \
                self.availability_zones(request)
            try:
                image = self.get_image(request,
                                       request.GET["image_id"])
                image.bytes = image.size
                self.fields['name'].initial = image.name
                min_vol_size = functions.bytes_to_gigabytes(
                    image.size)
                size_help_text = _('Volume size must be equal to or greater '
                                   'than the image size (%s)') \
                                 % filesizeformat(image.size)
                min_disk_size = getattr(image, 'min_disk', 0)
                if (min_disk_size > min_vol_size):
                    min_vol_size = min_disk_size
                    size_help_text = _('Volume size must be equal to or '
                                       'greater than the image minimum '
                                       'disk size (%sGB)') \
                                     % min_disk_size
                self.fields['size'].initial = min_vol_size
                self.fields['size'].help_text = size_help_text
                self.fields['image_source'].choices = ((image.id, image),)
                del self.fields['snapshot_source']
                del self.fields['volume_source']
                del self.fields['volume_source_type']
            except Exception:
                msg = _('Unable to load the specified image. %s')
                exceptions.handle(request, msg % request.GET['image_id'])
        elif 'volume_id' in request.GET:
            self.fields['availability_zone'].choices = \
                self.availability_zones(request)
            volume = None
            try:
                volume = self.get_volume(request, request.GET["volume_id"])
            except Exception:
                msg = _('Unable to load the specified volume. %s')
                exceptions.handle(request, msg % request.GET['volume_id'])

            if volume is not None:
                self.fields['name'].initial = volume.name
                self.fields['description'].initial = volume.description
                min_vol_size = volume.size
                size_help_text = _('Volume size must be equal to or greater '
                                   'than the origin volume size (%s)') \
                                 % filesizeformat(volume.size)
                self.fields['size'].initial = min_vol_size
                self.fields['size'].help_text = size_help_text
                self.fields['volume_source'].choices = ((volume.id, volume),)
                self.fields['type'].initial = volume.type
                del self.fields['snapshot_source']
                del self.fields['image_source']
                del self.fields['volume_source_type']
        else:
            source_type_choices = []
            self.fields['availability_zone'].choices = \
                self.availability_zones(request)

            try:
                snapshot_list = cinder.volume_snapshot_list(request)
                snapshots = [s for s in snapshot_list
                              if s.status == 'available']
                if snapshots:
                    source_type_choices.append(("snapshot_source",
                                                _("Snapshot")))
                    choices = [('', _("Choose a snapshot"))] + \
                              [(s.id, s) for s in snapshots]
                    self.fields['snapshot_source'].choices = choices
                else:
                    del self.fields['snapshot_source']
            except Exception:
                exceptions.handle(request, _("Unable to retrieve "
                        "volume snapshots."))

            images = utils.get_available_images(request,
                                          request.user.tenant_id)
            if images:
                source_type_choices.append(("image_source", _("Image")))
                choices = [('', _("Choose an image"))]
                for image in images:
                    image.bytes = image.size
                    image.size = functions.bytes_to_gigabytes(image.bytes)
                    choices.append((image.id, image))
                self.fields['image_source'].choices = choices
            else:
                del self.fields['image_source']

            volumes = self.get_volumes(request)
            if volumes:
                source_type_choices.append(("volume_source", _("Volume")))
                choices = [('', _("Choose a volume"))]
                for volume in volumes:
                    choices.append((volume.id, volume))
                self.fields['volume_source'].choices = choices
            else:
                del self.fields['volume_source']

            if source_type_choices:
                choices = ([('no_source_type',
                             _("No source, empty volume"))] +
                            source_type_choices)
                self.fields['volume_source_type'].choices = choices
            else:
                del self.fields['volume_source_type']

    # Determine whether the extension for Cinder AZs is enabled
    def cinder_az_supported(self, request):
        try:
            return cinder.extension_supported(request, 'AvailabilityZones')
        except Exception:
            exceptions.handle(request, _('Unable to determine if '
                                         'availability zones extension '
                                         'is supported.'))
            return False

    def availability_zones(self, request):
        zone_list = []
        if self.cinder_az_supported(request):
            try:
                zones = api.cinder.availability_zone_list(request)
                zone_list = [(zone.zoneName, zone.zoneName)
                              for zone in zones if zone.zoneState['available']]
                zone_list.sort()
            except Exception:
                exceptions.handle(request, _('Unable to retrieve availability '
                                             'zones.'))
        if not zone_list:
            zone_list.insert(0, ("", _("No availability zones found")))
        elif len(zone_list) > 0:
            zone_list.insert(0, ("", _("Any Availability Zone")))

        return zone_list

    def get_volumes(self, request):
        volumes = []
        try:
            volume_list = cinder.volume_list(self.request)
            if volume_list is not None:
                volumes = [v for v in volume_list
                           if v.status == api.cinder.VOLUME_STATE_AVAILABLE]
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve list of volumes.'))
        return volumes

    def handle(self, request, data):
        try:
            usages = quotas.tenant_limit_usages(self.request)
            availableGB = usages['maxTotalVolumeGigabytes'] - \
                usages['gigabytesUsed']
            availableVol = usages['maxTotalVolumes'] - usages['volumesUsed']

            snapshot_id = None
            image_id = None
            volume_id = None
            source_type = data.get('volume_source_type', None)
            az = data.get('availability_zone', None) or None
            if (data.get("snapshot_source", None) and
                  source_type in [None, 'snapshot_source']):
                # Create from Snapshot
                snapshot = self.get_snapshot(request,
                                             data["snapshot_source"])
                snapshot_id = snapshot.id
                if (data['size'] < snapshot.size):
                    error_message = _('The volume size cannot be less than '
                        'the snapshot size (%sGB)') % snapshot.size
                    raise ValidationError(error_message)
                az = None
            elif (data.get("image_source", None) and
                  source_type in [None, 'image_source']):
                # Create from Snapshot
                image = self.get_image(request,
                                       data["image_source"])
                image_id = image.id
                image_size = functions.bytes_to_gigabytes(image.size)
                if (data['size'] < image_size):
                    error_message = _('The volume size cannot be less than '
                        'the image size (%s)') % filesizeformat(image.size)
                    raise ValidationError(error_message)
                min_disk_size = getattr(image, 'min_disk', 0)
                if (min_disk_size > 0 and data['size'] < image.min_disk):
                    error_message = _('The volume size cannot be less than '
                        'the image minimum disk size (%sGB)') % min_disk_size
                    raise ValidationError(error_message)
            elif (data.get("volume_source", None) and
                  source_type in [None, 'volume_source']):
                # Create from volume
                volume = self.get_volume(request, data["volume_source"])
                volume_id = volume.id

                if data['size'] < volume.size:
                    error_message = _('The volume size cannot be less than '
                        'the source volume size (%sGB)') % volume.size
                    raise ValidationError(error_message)
            else:
                if type(data['size']) is str:
                    data['size'] = int(data['size'])

            if availableGB < data['size']:
                error_message = _('A volume of %(req)iGB cannot be created as '
                                  'you only have %(avail)iGB of your quota '
                                  'available.')
                params = {'req': data['size'],
                          'avail': availableGB}
                raise ValidationError(error_message % params)
            elif availableVol <= 0:
                error_message = _('You are already using all of your available'
                                  ' volumes.')
                raise ValidationError(error_message)

            metadata = {}

            volume = cinder.volume_create(request,
                                          data['size'],
                                          data['name'],
                                          data['description'],
                                          data['type'],
                                          snapshot_id=snapshot_id,
                                          image_id=image_id,
                                          metadata=metadata,
                                          availability_zone=az,
                                          source_volid=volume_id)
            message = _('Creating volume "%s"') % data['name']
            messages.info(request, message)
            return volume
        except ValidationError as e:
            self.api_error(e.messages[0])
            return False
        except Exception:
            exceptions.handle(request, ignore=True)
            self.api_error(_("Unable to create volume."))
            return False

    @memoized
    def get_snapshot(self, request, id):
        return cinder.volume_snapshot_get(request, id)

    @memoized
    def get_image(self, request, id):
        return glance.image_get(request, id)

    @memoized
    def get_volume(self, request, id):
        return cinder.volume_get(request, id)


class AttachForm(forms.SelfHandlingForm):
    instance = forms.ChoiceField(label=_("Attach to Instance"),
                                 help_text=_("Select an instance to "
                                             "attach to."))
    device = forms.CharField(label=_("Device Name"),
                             help_text=_("Actual device name may differ due "
                                         "to hypervisor settings."))

    def __init__(self, *args, **kwargs):
        super(AttachForm, self).__init__(*args, **kwargs)

        # Hide the device field if the hypervisor doesn't support it.
        hypervisor_features = getattr(settings,
                                      "OPENSTACK_HYPERVISOR_FEATURES",
                                      {})
        can_set_mount_point = hypervisor_features.get("can_set_mount_point",
                                                      False)
        if not can_set_mount_point:
            self.fields['device'].widget = forms.widgets.HiddenInput()
            self.fields['device'].required = False

        # populate volume_id
        volume = kwargs.get('initial', {}).get("volume", None)
        if volume:
            volume_id = volume.id
        else:
            volume_id = None
        self.fields['volume_id'] = forms.CharField(widget=forms.HiddenInput(),
                                                   initial=volume_id)

        # Populate instance choices
        instance_list = kwargs.get('initial', {}).get('instances', [])
        instances = []
        for instance in instance_list:
            if instance.status in tables.VOLUME_ATTACH_READY_STATES and \
                    not any(instance.id == att["server_id"]
                            for att in volume.attachments):
                instances.append((instance.id, '%s (%s)' % (instance.name,
                                                            instance.id)))
        if instances:
            instances.insert(0, ("", _("Select an instance")))
        else:
            instances = (("", _("No instances available")),)
        self.fields['instance'].choices = instances

    def handle(self, request, data):
        instance_choices = dict(self.fields['instance'].choices)
        instance_name = instance_choices.get(data['instance'],
                                             _("Unknown instance (None)"))
        # The name of the instance in the choices list has the ID appended to
        # it, so let's slice that off...
        instance_name = instance_name.rsplit(" (")[0]
        try:
            attach = api.nova.instance_volume_attach(request,
                                                     data['volume_id'],
                                                     data['instance'],
                                                     data.get('device', ''))
            volume = cinder.volume_get(request, data['volume_id'])
            message = _('Attaching volume %(vol)s to instance '
                         '%(inst)s on %(dev)s.') % {"vol": volume.name,
                                                    "inst": instance_name,
                                                    "dev": attach.device}
            messages.info(request, message)
            return True
        except Exception:
            redirect = reverse("horizon:project:volumes:index")
            exceptions.handle(request,
                              _('Unable to attach volume.'),
                              redirect=redirect)


class CreateSnapshotForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label=_("Snapshot Name"))
    description = forms.CharField(widget=forms.Textarea,
            label=_("Description"), required=False)

    def __init__(self, request, *args, **kwargs):
        super(CreateSnapshotForm, self).__init__(request, *args, **kwargs)

        # populate volume_id
        volume_id = kwargs.get('initial', {}).get('volume_id', [])
        self.fields['volume_id'] = forms.CharField(widget=forms.HiddenInput(),
                                                   initial=volume_id)

    def handle(self, request, data):
        try:
            volume = cinder.volume_get(request,
                                       data['volume_id'])
            force = False
            message = _('Creating volume snapshot "%s".') % data['name']
            if volume.status == 'in-use':
                force = True
                message = _('Forcing to create snapshot "%s" '
                            'from attached volume.') % data['name']
            snapshot = cinder.volume_snapshot_create(request,
                                                     data['volume_id'],
                                                     data['name'],
                                                     data['description'],
                                                     force=force)

            messages.info(request, message)
            return snapshot
        except Exception:
            redirect = reverse("horizon:project:volumes:index")
            exceptions.handle(request,
                              _('Unable to create volume snapshot.'),
                              redirect=redirect)


class UpdateForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label=_("Volume Name"))
    description = forms.CharField(widget=forms.Textarea,
            label=_("Description"), required=False)

    def handle(self, request, data):
        volume_id = self.initial['volume_id']
        try:
            cinder.volume_update(request, volume_id, data['name'],
                                 data['description'])

            message = _('Updating volume "%s"') % data['name']
            messages.info(request, message)
            return True
        except Exception:
            redirect = reverse("horizon:project:volumes:index")
            exceptions.handle(request,
                              _('Unable to update volume.'),
                              redirect=redirect)


class ExtendForm(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Volume Name"),
                           widget=forms.TextInput(
                               attrs={'readonly': 'readonly'}
                           ))
    new_size = forms.IntegerField(min_value=1, label=_("Size (GB)"))

    def clean(self):
        cleaned_data = super(ExtendForm, self).clean()
        new_size = cleaned_data.get('new_size', 1)
        if new_size <= self.initial['orig_size']:
            raise ValidationError(
                _("New size for extend must be greater than current size."))

        return cleaned_data

    def handle(self, request, data):
        volume_id = self.initial['id']
        try:
            volume = cinder.volume_extend(request,
                                          volume_id,
                                          data['new_size'])

            message = _('Successfully extended volume: "%s"') % data['name']
            messages.success(request, message)
            return volume
        except Exception:
            redirect = reverse("horizon:project:volumes:index")
            exceptions.handle(request,
                              _('Unable to extend volume.'),
                              redirect=redirect)
