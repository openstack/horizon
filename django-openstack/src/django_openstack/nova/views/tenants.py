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
Views for managing Nova projects.
"""
import logging

from django import http
from django import template
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render_to_response
from django_openstack.nova import forms as nova_forms
from django_openstack.nova.exceptions import handle_nova_error
#from django_openstack.nova.shortcuts import get_project_or_404

from django_openstack import api


LOG = logging.getLogger('django_openstack.nova')


@login_required
@handle_nova_error
def detail(request, tenant_id):
    tenant = api.get_tenant(request, request.user.tenant)
    instances = api.compute_api(request).servers.list()

    return render_to_response(
        'django_openstack/nova/tenants/index.html',
        {'tenant': tenant,
         'instance_count': len(instances)},
        context_instance=template.RequestContext(request))


@login_required
@handle_nova_error
def manage(request, project_id):
    project = get_project_or_404(request, project_id)

    if project.projectManagerId != request.user.username:
        return redirect('login')

    nova = get_nova_admin_connection()
    members = nova.get_project_members(project_id)

    for member in members:
        project_role = [str(role.role) for role in
                        nova.get_user_roles(member.memberId, project_id)]
        global_role = [str(role.role) for role in
                       nova.get_user_roles(member.memberId, project=False)]

        member.project_roles = ", ".join(project_role)
        member.global_roles = ", ".join(global_role)

    return render_to_response(
        'django_openstack/nova/projects/manage.html',
        {'project': project,
         'members': members},
        context_instance=template.RequestContext(request))
