# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 Nebula, Inc.
# All rights reserved.

"""
Views for managing Nova volumes.
"""

import logging

from django import shortcuts
from django.contrib import messages
from django.utils.translation import ugettext as _

from horizon import api
from horizon import forms
from novaclient import exceptions as novaclient_exceptions


LOG = logging.getLogger(__name__)


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
            LOG.info(message)
            messages.info(request, message)
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in CreateVolume")
            messages.error(request,
                           _('Error Creating Volume: %s') % e.message)
        return shortcuts.redirect("horizon:nova:instances_and_volumes:index")


class AttachForm(forms.SelfHandlingForm):
    instance = forms.ChoiceField(label="Attach to Instance",
                                 help_text=_("Select an instance to "
                                             "attach to."))
    device = forms.CharField(label="Device Name", initial="/dev/vdb")

    def __init__(self, *args, **kwargs):
        super(AttachForm, self).__init__(*args, **kwargs)
        # populate volume_id
        volume_id = kwargs.get('initial', {}).get('volume_id', [])
        self.fields['volume_id'] = forms.CharField(widget=forms.HiddenInput(),
                                                   initial=volume_id)

        # Populate instance choices
        instance_list = kwargs.get('initial', {}).get('instances', [])
        instances = [('', "Select an instance")]
        for instance in instance_list:
            instances.append((instance.id, '%s (%s)' % (instance.name,
                                                        instance.id)))
        self.fields['instance'].choices = instances

    def handle(self, request, data):
        try:
            api.volume_attach(request,
                              data['volume_id'],
                              data['instance'],
                              data['device'])
            vol_name = api.volume_get(request, data['volume_id']).displayName

            message = (_('Attaching volume %(vol)s to instance \
                            %(inst)s at %(dev)s') %
                            {"vol": vol_name, "inst": data['instance'],
                            "dev": data['device']})
            LOG.info(message)
            messages.info(request, message)
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in AttachVolume")
            messages.error(request,
                           _('Error attaching volume: %s') % e.message)
        return shortcuts.redirect(
                            "horizon:nova:instances_and_volumes:index")
