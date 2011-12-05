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
        return shortcuts.redirect(
                            "horizon:nova:instances_and_volumes:volumes:index")


class DeleteForm(forms.SelfHandlingForm):
    volume_id = forms.CharField(widget=forms.HiddenInput())
    volume_name = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            api.volume_delete(request, data['volume_id'])
            message = 'Deleting volume "%s"' % data['volume_id']
            LOG.info(message)
            messages.info(request, message)
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in DeleteVolume")
            messages.error(request,
                           _('Error deleting volume: %s') % e.message)
        return shortcuts.redirect(request.build_absolute_uri())


class AttachForm(forms.SelfHandlingForm):
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
        self.fields['instance'] = forms.ChoiceField(
                                  choices=instances,
                                  label="Attach to Instance",
                                  help_text="Select an instance to attach to.")

    def handle(self, request, data):
        try:
            api.volume_attach(request,
                              data['volume_id'],
                              data['instance'],
                              data['device'])
            vol_name = api.volume_get(request, data['volume_id']).displayName

            message = (_('Attaching volume %s to instance %s at %s') %
                            (vol_name, data['instance'],
                             data['device']))
            LOG.info(message)
            messages.info(request, message)
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in AttachVolume")
            messages.error(request,
                           _('Error attaching volume: %s') % e.message)
        return shortcuts.redirect(
                            "horizon:nova:instances_and_volumes:volumes:index")


class DetachForm(forms.SelfHandlingForm):
    volume_id = forms.CharField(widget=forms.HiddenInput())
    instance_id = forms.CharField(widget=forms.HiddenInput())
    attachment_id = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            api.volume_detach(request, data['instance_id'],
                              data['attachment_id'])
            message = (_('Detaching volume %s from instance %s') %
                    (data['volume_id'], data['instance_id']))
            LOG.info(message)
            messages.info(request, message)
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in DetachVolume")
            messages.error(request,
                           _('Error detaching volume: %s') % e.message)
        return shortcuts.redirect(
                            "horizon:nova:instances_and_volumes:volumes:index")
