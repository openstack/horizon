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

from django import template
from django.shortcuts import render_to_response
from django.views.decorators.vary import vary_on_cookie
from django_openstack.nova.shortcuts import get_projects
from django_openstack.nova.exceptions import handle_nova_error


@vary_on_cookie
@handle_nova_error
def index(request):
    projects = None
    page_type = "home"

    if request.user.is_authenticated():
        projects = get_projects(user=request.user)

    return render_to_response('index.html', {
        'projects': projects,
        'page_type': page_type,
    }, context_instance=template.RequestContext(request))
