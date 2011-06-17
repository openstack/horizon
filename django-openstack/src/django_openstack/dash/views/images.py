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


class LaunchForm(forms.SelfHandlingForm):
    image_id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=80, label="Server Name")

    # make the dropdown populate when the form is loaded not when django is
    # started
    def __init__(self, *args, **kwargs):
        super(LaunchForm, self).__init__(*args, **kwargs)
        flavorlist = kwargs.get('initial', {}).get('flavorlist', [])
        self.fields['flavor'] = forms.ChoiceField(
                choices=flavorlist,
                label="Flavor",
                help_text="Size of Image to launch")

    def handle(self, request, data):
        image_id = data['image_id']
        try:
            image = api.compute_api(request).images.get(image_id)
            flavor = api.compute_api(request).flavors.get(data['flavor'])
            api.compute_api(request).servers.create(data['name'],
                                                    image,
                                                    flavor)
            messages.success(request, "Instance was successfully\
                                       launched.")
            return shortcuts.redirect(request.build_absolute_uri())

        except api_exceptions.ApiException, e:
            messages.error(request,
                           'Unable to launch instance: %s' % e.message)


@login_required
def index(request, tenant_id):
    tenant = api.get_tenant(request, request.user.tenant)
    images = api.glance_api(request).get_images_detailed()

    return render_to_response('dash_images.html', {
        'tenant': tenant,
        'images': images,
        #'image_lists': _image_lists(images, request.user.tenant),
    }, context_instance=template.RequestContext(request))


@login_required
def launch(request, tenant_id, image_id):
    def flavorlist():
        try:
            fl = api.extras_api(request).flavors.list()

            # TODO add vcpu count to flavors
            sel = [(f.id, '%s (%svcpu / %sGB Disk / %sMB Ram )' %
                   (f.name, f.vcpus, f.disk, f.ram)) for f in fl]
            return sorted(sel)
        except:
            return [(1, 'm1.tiny')]

    image = api.compute_api(request).images.get(image_id)
    tenant = api.get_tenant(request, request.user.tenant)

    form, handled = LaunchForm.maybe_handle(
            request, initial={'flavorlist': flavorlist(),
                              'image_id': image_id})
    if handled:
        return handled

    return render_to_response('dash_launch.html', {
        'tenant': tenant,
        'image': image,
        'form': form,
    }, context_instance=template.RequestContext(request))
