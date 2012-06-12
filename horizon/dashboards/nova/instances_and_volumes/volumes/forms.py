# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nebula, Inc.
# All rights reserved.

"""
Views for managing Nova volumes.
"""

from django import shortcuts
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import forms
from horizon import exceptions

from ..instances.tables import ACTIVE_STATES


class CreateForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label="Volume Name")
    description = forms.CharField(widget=forms.Textarea,
            label=_("Description"), required=False)
    size = forms.IntegerField(min_value=1, label="Size (GB)")

    def handle(self, request, data):
        try:
            api.volume_create(request, data['size'], data['name'],
                              data['description'])
            message = 'Creating volume "%s"' % data['name']
            messages.info(request, message)
        except:
            exceptions.handle(request,
                              _("Unable to create volume."))
        return shortcuts.redirect("horizon:nova:instances_and_volumes:index")


class AttachForm(forms.SelfHandlingForm):
    instance = forms.ChoiceField(label="Attach to Instance",
                                 help_text=_("Select an instance to "
                                             "attach to."))
    device = forms.CharField(label="Device Name", initial="/dev/vdc")

    def __init__(self, *args, **kwargs):
        super(AttachForm, self).__init__(*args, **kwargs)
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
            if instance.status in ACTIVE_STATES and \
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
            api.volume_attach(request,
                              data['volume_id'],
                              data['instance'],
                              data['device'])
            vol_name = api.volume_get(request, data['volume_id']).display_name

            message = _('Attaching volume %(vol)s to instance '
                         '%(inst)s on %(dev)s.') % {"vol": vol_name,
                                                    "inst": instance_name,
                                                    "dev": data['device']}
            messages.info(request, message)
        except:
            exceptions.handle(request,
                              _('Unable to attach volume.'))
        return shortcuts.redirect(
                            "horizon:nova:instances_and_volumes:index")


class CreateSnapshotForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label=_("Snapshot Name"))
    description = forms.CharField(widget=forms.Textarea,
            label=_("Description"), required=False)

    def __init__(self, *args, **kwargs):
        super(CreateSnapshotForm, self).__init__(*args, **kwargs)

        # populate volume_id
        volume_id = kwargs.get('initial', {}).get('volume_id', [])
        self.fields['volume_id'] = forms.CharField(widget=forms.HiddenInput(),
                                                   initial=volume_id)

    def handle(self, request, data):
        try:
            api.volume_snapshot_create(request,
                                       data['volume_id'],
                                       data['name'],
                                       data['description'])

            message = _('Creating volume snapshot "%s"') % data['name']
            messages.info(request, message)
        except:
            exceptions.handle(request,
                              _('Unable to create volume snapshot.'))

        return shortcuts.redirect("horizon:nova:images_and_snapshots:index")
