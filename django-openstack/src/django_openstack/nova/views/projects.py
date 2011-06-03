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

from django import http
from django import template
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render_to_response
from django_openstack.core.connection import get_nova_admin_connection
from django_openstack import log as logging
from django_openstack.nova import forms as nova_forms
from django_openstack.nova.exceptions import handle_nova_error
from django_openstack.nova.shortcuts import get_project_or_404


LOG = logging.getLogger('django_openstack.nova')


@login_required
@handle_nova_error
def detail(request, project_id):
    project = get_project_or_404(request, project_id)

    return render_to_response(
        'django_openstack/nova/projects/index.html',
        {'project': project,
         'instance_count': project.get_instance_count()},
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


@login_required
@handle_nova_error
def edit_user(request, project_id, username):
    nova = get_nova_admin_connection()
    project = get_project_or_404(request, project_id)
    user = nova.get_user(username)
    userroles = nova.get_user_roles(username, project_id)

    if project.projectManagerId != request.user.username:
        return redirect('login')

    if request.method == 'POST':
        form = nova_forms.ProjectUserForm(project, user, request.POST)
        if form.is_valid():
            form.save()
            LOG.info('Roles for user "%s" on project "%s" changed to "%s' %
                     (str(user), project_id,
                      ",".join(form.cleaned_data['role'])))

            return redirect('nova_project_manage',  project_id)
    else:
        roles = [str(role.role) for role in userroles]
        form = nova_forms.ProjectUserForm(project,
                                          user,
                                          {'role': roles,
                                           'user': user})

    return render_to_response(
        'django_openstack/nova/projects/edit_user.html',
        {'form': form,
         'project': project,
         'user': user},
        context_instance=template.RequestContext(request))


@login_required
@handle_nova_error
def download_credentials(request, project_id):
    project = get_project_or_404(request, project_id)

    response = http.HttpResponse(mimetype='application/zip')
    response['Content-Disposition'] = \
        'attachment; filename=%s-%s-%s-x509.zip' % \
        (settings.SITE_NAME, project.projectname, request.user)
    response.write(project.get_zip())

    return response
