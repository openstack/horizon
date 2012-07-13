# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nebula, Inc.
# All rights reserved.

"""
Views for managing Nova volumes.
"""

from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import forms
from horizon import exceptions
from horizon import messages

from ..instances.tables import ACTIVE_STATES


class CreateForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label="Volume Name")
    description = forms.CharField(widget=forms.Textarea,
            label=_("Description"), required=False)
    size = forms.IntegerField(min_value=1, label="Size (GB)")

    def handle(self, request, data):
        try:
            # FIXME(johnp): Nova (cinderclient) currently returns a useless
            # error message when the quota is exceeded when trying to create
            # a volume, so we need to check for that scenario here before we
            # send it off to Nova to try and create.
            usages = api.tenant_quota_usages(request)

            if type(data['size']) is str:
                data['size'] = int(data['size'])

            if usages['gigabytes']['available'] < data['size']:
                error_message = _('A volume of %(req)iGB cannot be created as '
                                  'you only have %(avail)iGB of your quota '
                                  'available.')
                params = {'req': data['size'],
                          'avail': usages['gigabytes']['available']}
                raise ValidationError(error_message % params)
            elif usages['volumes']['available'] <= 0:
                error_message = _('You are already using all of your available'
                                  ' volumes.')
                raise ValidationError(error_message)

            volume = api.volume_create(request,
                                       data['size'],
                                       data['name'],
                                       data['description'])
            message = 'Creating volume "%s"' % data['name']
            messages.info(request, message)
            return volume
        except ValidationError, e:
            return self.api_error(e.messages[0])
        except:
            exceptions.handle(request, ignore=True)
            return self.api_error(_("Unable to create volume."))


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
            return True
        except:
            redirect = reverse("horizon:nova:volumes:index")
            exceptions.handle(request,
                              _('Unable to attach volume.'),
                              redirect=redirect)


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
            snapshot = api.volume_snapshot_create(request,
                                                  data['volume_id'],
                                                  data['name'],
                                                  data['description'])

            message = _('Creating volume snapshot "%s"') % data['name']
            messages.info(request, message)
            return snapshot
        except:
            redirect = reverse("horizon:nova:images_and_snapshots:index")
            exceptions.handle(request,
                              _('Unable to create volume snapshot.'),
                              redirect=redirect)
