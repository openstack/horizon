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
Views for home page.
"""
import logging

from django import template
from django.shortcuts import render_to_response
from django.views.decorators.vary import vary_on_cookie

from django import shortcuts

from django_openstack import api
from django_openstack.nova import forms as nova_forms


from django_openstack.nova.exceptions import handle_nova_error


@vary_on_cookie
@handle_nova_error
def splash(request):
    if request.user:
        if request.user.is_admin():
            return shortcuts.redirect('admin_overview')
        else:
            return shortcuts.redirect('dash_overview')

    return render_to_response('splash.html', {
        'login_form': nova_forms.Login(),
    }, context_instance=template.RequestContext(request))


# login_required
def user_overview(request, tenant_id=None):
    return render_to_response('dash_overview.html', {

    }, context_instance=template.RequestContext(request))
