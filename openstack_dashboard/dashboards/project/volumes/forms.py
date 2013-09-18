# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nebula, Inc.
# All rights reserved.

"""
Views for managing volumes.
"""

from django.conf import settings  # noqa
from django.core.urlresolvers import reverse  # noqa
from django.forms import ValidationError  # noqa
from django.template.defaultfilters import filesizeformat  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import fields
from horizon.utils import functions
from horizon.utils.memoized import memoized  # noqa

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.api import glance
from openstack_dashboard.dashboards.project.images_and_snapshots import utils
from openstack_dashboard.dashboards.project.instances import tables
from openstack_dashboard.usage import quotas


class CreateForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label=_("Volume Name"))
    description = forms.CharField(widget=forms.Textarea,
            label=_("Description"), required=False)
    type = forms.ChoiceField(label=_("Type"),
                             required=False)
    size = forms.IntegerField(min_value=1, label=_("Size (GB)"))
    volume_source_type = forms.ChoiceField(label=_("Volume Source"),
                                           required=False)
    snapshot_source = forms.ChoiceField(
        label=_("Use snapshot as a source"),
        widget=fields.SelectWidget(
            attrs={'class': 'snapshot-selector'},
            data_attrs=('size', 'display_name'),
            transform=lambda x: "%s (%sGB)" % (x.display_name, x.size)),
        required=False)
    image_source = forms.ChoiceField(
        label=_("Use image as a source"),
        widget=fields.SelectWidget(
            attrs={'class': 'image-selector'},
            data_attrs=('size', 'name'),
            transform=lambda x: "%s (%s)" % (x.name, filesizeformat(x.bytes))),
        required=False)

    def __init__(self, request, *args, **kwargs):
        super(CreateForm, self).__init__(request, *args, **kwargs)
        volume_types = cinder.volume_type_list(request)
        self.fields['type'].choices = [("", "")] + \
                                      [(type.name, type.name)
                                       for type in volume_types]

        if ("snapshot_id" in request.GET):
            try:
                snapshot = self.get_snapshot(request,
                                             request.GET["snapshot_id"])
                self.fields['name'].initial = snapshot.display_name
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
                                'to or greater than the snapshot size (%sGB)'
                                % snapshot.size)
                del self.fields['image_source']
                del self.fields['volume_source_type']
            except Exception:
                exceptions.handle(request,
                                  _('Unable to load the specified snapshot.'))
        elif ('image_id' in request.GET):
            try:
                image = self.get_image(request,
                                       request.GET["image_id"])
                image.bytes = image.size
                self.fields['name'].initial = image.name
                self.fields['size'].initial = functions.bytes_to_gigabytes(
                    image.size)
                self.fields['image_source'].choices = ((image.id, image),)
                self.fields['size'].help_text = _('Volume size must be equal '
                                'to or greater than the image size (%s)'
                                % filesizeformat(image.size))
                del self.fields['snapshot_source']
                del self.fields['volume_source_type']
            except Exception:
                msg = _('Unable to load the specified image. %s')
                exceptions.handle(request, msg % request.GET['image_id'])
        else:
            source_type_choices = []

            try:
                snapshots = cinder.volume_snapshot_list(request)
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

            if source_type_choices:
                choices = ([('no_source_type',
                             _("No source, empty volume."))] +
                            source_type_choices)
                self.fields['volume_source_type'].choices = choices
            else:
                del self.fields['volume_source_type']

    def handle(self, request, data):
        try:
            usages = quotas.tenant_limit_usages(self.request)
            availableGB = usages['maxTotalVolumeGigabytes'] - \
                usages['gigabytesUsed']
            availableVol = usages['maxTotalVolumes'] - usages['volumesUsed']

            snapshot_id = None
            image_id = None
            source_type = data.get('volume_source_type', None)
            if (data.get("snapshot_source", None) and
                  source_type in [None, 'snapshot_source']):
                # Create from Snapshot
                snapshot = self.get_snapshot(request,
                                             data["snapshot_source"])
                snapshot_id = snapshot.id
                if (data['size'] < snapshot.size):
                    error_message = _('The volume size cannot be less than '
                                      'the snapshot size (%sGB)' %
                                      snapshot.size)
                    raise ValidationError(error_message)
            elif (data.get("image_source", None) and
                  source_type in [None, 'image_source']):
                # Create from Snapshot
                image = self.get_image(request,
                                       data["image_source"])
                image_id = image.id
                image_size = functions.bytes_to_gigabytes(image.size)
                if (data['size'] < image_size):
                    error_message = _('The volume size cannot be less than '
                                      'the image size (%s)' %
                                      filesizeformat(image.size))
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
                                          metadata=metadata)
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


class AttachForm(forms.SelfHandlingForm):
    instance = forms.ChoiceField(label=_("Attach to Instance"),
                                 help_text=_("Select an instance to "
                                             "attach to."))
    device = forms.CharField(label=_("Device Name"))

    def __init__(self, *args, **kwargs):
        super(AttachForm, self).__init__(*args, **kwargs)

        # Hide the device field if the hypervisor doesn't support it.
        hypervisor_features = getattr(settings,
                                      "OPENSTACK_HYPERVISOR_FEATURES",
                                      {})
        can_set_mount_point = hypervisor_features.get("can_set_mount_point",
                                                      True)
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
            if instance.status in tables.ACTIVE_STATES and \
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
            if not volume.display_name:
                volume_name = volume.id
            else:
                volume_name = volume.display_name
            message = _('Attaching volume %(vol)s to instance '
                         '%(inst)s on %(dev)s.') % {"vol": volume_name,
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
            snapshot = cinder.volume_snapshot_create(request,
                                                     data['volume_id'],
                                                     data['name'],
                                                     data['description'])

            message = _('Creating volume snapshot "%s"') % data['name']
            messages.info(request, message)
            return snapshot
        except Exception:
            redirect = reverse("horizon:project:images_and_snapshots:index")
            exceptions.handle(request,
                              _('Unable to create volume snapshot.'),
                              redirect=redirect)
