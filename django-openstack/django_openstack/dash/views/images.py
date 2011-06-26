# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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
Views for managing Nova images.
"""

import datetime
import logging
import re

from django import http
from django import template
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render_to_response
from django.utils.translation import ugettext as _
from django import shortcuts

from django_openstack import api
from django_openstack import forms
from openstackx.api import exceptions as api_exceptions
from glance.common import exception as glance_exception


LOG = logging.getLogger('django_openstack.dash')

from django.core import validators
import re


def validate_even(value):
    if value % 2 != 0:
        raise ValidationError(u'%s is not an even number' % value)


class LaunchForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length=80, label="Server Name")
    image_id = forms.CharField(widget=forms.HiddenInput())
    tenant_id = forms.CharField(widget=forms.HiddenInput())
    user_data = forms.CharField(widget=forms.Textarea,
                                label="User Data",
                                required=False)
    name = forms.CharField(max_length=80, label="Server Name")

    security_groups = forms.CharField(max_length=100, validators=[validators.RegexValidator(regex=re.compile(r'^[0-9A-Za-z,]*$'))], required=False)

    # make the dropdown populate when the form is loaded not when django is
    # started
    def __init__(self, *args, **kwargs):
        super(LaunchForm, self).__init__(*args, **kwargs)
        flavorlist = kwargs.get('initial', {}).get('flavorlist', [])
        self.fields['flavor'] = forms.ChoiceField(
                choices=flavorlist,
                label="Flavor",
                help_text="Size of Image to launch")

        keynamelist = kwargs.get('initial', {}).get('keynamelist', [])
        self.fields['key_name'] = forms.ChoiceField(choices=keynamelist,
                label="Key Name",
                required=False,
                help_text="Which keypair to use for authentication")

#        self.fields.keyOrder = [
#            'name',
#            'user_data',
#            'security_groups',
#            'flavor',
#            'key_name']
#

    def handle(self, request, data):
        image_id = data['image_id']
        tenant_id = data['tenant_id']
        try:
            image = api.image_get(request, image_id)
            flavor = api.flavor_get(request, data['flavor'])
            api.server_create(request,
                              data['name'],
                              image,
                              flavor,
                              user_data=data['user_data'],
                              key_name=data.get('key_name'),
                              security_groups=data.get('security_groups').split(','))

            messages.success(request, "Instance was successfully\
                                       launched.")
            return redirect('dash_instances', tenant_id)

        except api_exceptions.ApiException, e:
            messages.error(request,
                           'Unable to launch instance: %s' % e.message)


@login_required
def index(request, tenant_id):
    tenant = api.token_get_tenant(request, request.user.tenant)
    all_images = []
    try:
        all_images = api.image_list_detailed(request)
        if not all_images:
            messages.info(request, "There are currently no images.")
    except GlanceClientConnectionError, e:
        messages.error(request, "Error connecting to glance: %s" % e.message)
    except glance_exception.Error, e:
        messages.error(request, "Error retrieving image list: %s" % e.message)

    images = []

    def convert_time(tstr):
        if tstr:
            return datetime.datetime.strptime(tstr, "%Y-%m-%dT%H:%M:%S.%f")
        else:
            return ''

    for im in all_images:
        im['created'] = convert_time(im['created_at'])
        im['updated'] = convert_time(im['updated_at'])
        if im['container_format'] not in ['aki', 'ari']:
            images.append(im)

    return render_to_response('dash_images.html', {
        'tenant': tenant,
        'images': images,
    }, context_instance=template.RequestContext(request))


@login_required
def launch(request, tenant_id, image_id):
    def flavorlist():
        try:
            fl = api.flavor_list(request)

            # TODO add vcpu count to flavors
            sel = [(f.id, '%s (%svcpu / %sGB Disk / %sMB Ram )' %
                   (f.name, f.vcpus, f.disk, f.ram)) for f in fl]
            return sorted(sel)
        except:
            return [(1, 'm1.tiny')]

    def keynamelist():
        try:
            fl = api.keypair_list(request)
            sel = [(f.key_name, f.key_name) for f in fl]
            return sel
        except:
            return []

    image = api.image_get(request, image_id)
    tenant = api.token_get_tenant(request, request.user.tenant)

    form, handled = LaunchForm.maybe_handle(
            request, initial={'flavorlist': flavorlist(),
                              'keynamelist': keynamelist(),
                              'image_id': image_id,
                              'tenant_id': tenant_id})
    if handled:
        return handled

    return render_to_response('dash_launch.html', {
        'tenant': tenant,
        'image': image,
        'form': form,
    }, context_instance=template.RequestContext(request))
