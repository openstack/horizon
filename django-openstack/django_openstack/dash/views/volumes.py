# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 Nebula, Inc.
# All rights reserved.

"""
Views for managing Nova volumes.
"""

import logging

from django import template
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render_to_response
from django.utils.translation import ugettext as _

from django_openstack import api
from django_openstack import forms
from novaclient import exceptions as novaclient_exceptions


LOG = logging.getLogger('django_openstack.dash.views.volumes')


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
        return redirect(request.build_absolute_uri())


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
        return redirect(request.build_absolute_uri())


class AttachForm(forms.SelfHandlingForm):
    volume_id = forms.CharField(widget=forms.HiddenInput())
    device = forms.CharField(label="Device Name", initial="/dev/vdb")

    def __init__(self, *args, **kwargs):
        super(AttachForm, self).__init__(*args, **kwargs)
        instance_list = kwargs.get('initial', {}).get('instance_list', [])
        self.fields['instance'] = forms.ChoiceField(
                choices=instance_list,
                label="Attach to Instance",
                help_text="Select an instance to attach to.")

    def handle(self, request, data):
        try:
            api.volume_attach(request, data['volume_id'], data['instance'],
                              data['device'])
            message = (_('Attaching volume %s to instance %s at %s') %
                            (data['volume_id'], data['instance'],
                             data['device']))
            LOG.info(message)
            messages.info(request, message)
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in AttachVolume")
            messages.error(request,
                           _('Error attaching volume: %s') % e.message)
        return redirect(request.build_absolute_uri())


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
        return redirect(request.build_absolute_uri())


@login_required
def index(request, tenant_id):
    delete_form, handled = DeleteForm.maybe_handle(request)
    detach_form, handled = DetachForm.maybe_handle(request)

    if handled:
        return handled

    try:
        volumes = api.volume_list(request)
    except novaclient_exceptions.ClientException, e:
        volumes = []
        LOG.exception("ClientException in volume index")
        messages.error(request, _('Error fetching volumes: %s') % e.message)

    return render_to_response('django_openstack/dash/volumes/index.html', {
            'volumes': volumes, 'delete_form': delete_form,
            'detach_form': detach_form
    }, context_instance=template.RequestContext(request))


@login_required
def detail(request, tenant_id, volume_id):
    try:
        volume = api.volume_get(request, volume_id)
        attachment = volume.attachments[0]
        if attachment:
            instance = api.server_get(
                    request, volume.attachments[0]['serverId'])
        else:
            instance = None
    except novaclient_exceptions.ClientException, e:
        LOG.exception("ClientException in volume get")
        messages.error(request, _('Error fetching volume: %s') % e.message)
        return redirect('dash_volumes', tenant_id)

    return render_to_response('django_openstack/dash/volumes/detail.html', {
            'volume': volume,
            'attachment': attachment,
            'instance': instance
    }, context_instance=template.RequestContext(request))


@login_required
def create(request, tenant_id):
    create_form, handled = CreateForm.maybe_handle(request)

    if handled:
        return handled

    return render_to_response('django_openstack/dash/volumes/create.html', {
        'create_form': create_form
    }, context_instance=template.RequestContext(request))


@login_required
def attach(request, tenant_id, volume_id):

    def instances():
        insts = api.server_list(request)
        return [(inst.id, '%s (Instance %s)' % (inst.name, inst.id))
                for inst in insts]

    attach_form, handled = AttachForm.maybe_handle(
            request, initial={'instance_list': instances()})

    if handled:
        return handled

    return render_to_response('django_openstack/dash/volumes/attach.html', {
        'attach_form': attach_form, 'volume_id': volume_id
    }, context_instance=template.RequestContext(request))
