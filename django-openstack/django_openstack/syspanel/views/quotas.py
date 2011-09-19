# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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

from operator import itemgetter

from django import template
from django import http
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.shortcuts import render_to_response
from openstackx.api import exceptions as api_exceptions


from django_openstack import api
from django_openstack import forms
from django_openstack.decorators import enforce_admin_access


@login_required
@enforce_admin_access
def index(request):
    quotas = api.admin_api(request).quota_sets.get(True)._info
    quotas['ram'] = int(quotas['ram']) / 100
    quotas.pop('id')

    return render_to_response(
    'django_openstack/syspanel/quotas/index.html', {
        'quotas': quotas,
    }, context_instance=template.RequestContext(request))
