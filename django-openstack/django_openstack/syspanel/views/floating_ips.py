# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Fourth Paradigm Development, Inc.
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
Views for managing Nova floating ips.
"""
import logging

from django import http
from django import template
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import validators
from django import shortcuts
from django.shortcuts import redirect, render_to_response
from django.utils.translation import ugettext as _

from django_openstack import api
from django_openstack import forms
import openstackx.api.exceptions as api_exceptions


LOG = logging.getLogger('django_openstack.syspanel.views.floating_ip')

@login_required
def index(request):
    try:
        floating_ips = [api.admin_floating_ip_get(request, ip.id) 
                        for ip in api.admin_floating_ip_list(request)]
    except api_exceptions.ApiException, e:
        floating_ips = []
        LOG.error("ApiException in floating ip index", exc_info=True)
        messages.error(request, 'Error fetching floating ips: %s' % e.message)

    return shortcuts.render_to_response('syspanel_floating_ips.html', {
        'floating_ips': floating_ips,
    }, context_instance=template.RequestContext(request))
