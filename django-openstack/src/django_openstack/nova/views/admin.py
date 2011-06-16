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
Views for managing Nova through the Django admin interface.
"""

import boto.exception

from django import http
from django import template
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import models as auth_models
from django.shortcuts import redirect, render_to_response
from django.utils.translation import ugettext as _
from django_openstack import log as logging
from django_openstack import models
from django_openstack.core.connection import get_nova_admin_connection
from django_openstack.nova import forms


LOG = logging.getLogger('django_openstack.nova')


@staff_member_required
def project_sendcredentials(request, project_id):
    nova = get_nova_admin_connection()
    project = nova.get_project(project_id)

    users = [user.memberId for user in nova.get_project_members(project_id)]
    form = forms.SendCredentialsForm(query_list=users)

    if project == None:
        LOG.error("Project id %s not found" % project_id)
        raise http.Http404()

    if request.method == 'POST':
        if len(request.POST.getlist('users')) < 1:
            msg = "Please select a user to send credentials to."

            return render_to_response(
                'admin/django_openstack/nova/project/send_credentials.html',
                {'project': project,
                 'form': form,
                 'users': users,
                 'error': msg},
                context_instance=template.RequestContext(request))
        else:
            for username in request.POST.getlist('users'):
                models.CredentialsAuthorization.authorize(username, project_id)
            msg = "Credentials were successfully sent."
            return render_to_response(
                'admin/django_openstack/nova/project/send_credentials.html',
                {'project': project,
                 'form': form,
                 'users': users,
                 'success': msg},
                context_instance=template.RequestContext(request))

    return render_to_response(
        'admin/django_openstack/nova/project/send_credentials.html',
        {'project': project,
         'form': form,
         'users': users},
        context_instance=template.RequestContext(request))


@staff_member_required
def project_start_vpn(request, project_id):
    nova = get_nova_admin_connection()
    project = nova.get_project(project_id)

    if project == None:
        LOG.error("Project id %s does not exist" % project_id)
        raise http.Http404()

    try:
        nova.start_vpn(project_id)
        messages.success(request,
                       _('Successfully started VPN for project %(proj)s.') %
                         {'proj': project_id})
        LOG.info('Successfully started VPN for project %s.' % project_id)
    except boto.exception.EC2ResponseError, e:
        msg = _('Unable to start VPN for the project %(proj)s: %(code)s - %(msg)s' %
               {'proj': project_id,
               'code': e.code,
               'msg': e.error_message})
        messages.error(request, msg)
        LOG.error(msg)

    return redirect('admin_projects')


@staff_member_required
def projects_list(request):
    nova = get_nova_admin_connection()
    projects = nova.get_projects()

    return render_to_response(
        'admin/django_openstack/nova/project/project_list.html',
        {'projects': projects},
        context_instance=template.RequestContext(request))


@staff_member_required
def project_view(request, project_name):
    nova = get_nova_admin_connection()
    project = nova.get_project(project_name)
    users = nova.get_project_members(project_name)

    try:
        manager = auth_models.User.objects.get(
                username=project.projectManagerId)
    except auth_models.User.DoesNotExist:
        manager = None

    if request.method == 'POST':
        form = forms.ProjectForm(request.POST)
        if form.is_valid():
            try:
                nova.modify_project(form.cleaned_data["projectname"],
                                    form.cleaned_data["manager"],
                                    form.cleaned_data["description"])
                msg = _('Successfully modified the project %(proj)s.' %
                        {'proj': project_name})
                messages.success(request, msg)
                LOG.info(msg)
            except boto.exception.EC2ResponseError, e:
                msg = _('Unable modify the project %(proj)s: %(code)s - %(msg)s' %
                        {'proj': project_name,
                        'code': e.code,
                        'msg': e.error_message})
                messages.error(request, msg)
                LOG.error(msg)

            return redirect('admin_project', request.POST["projectname"])
    else:
        form = forms.ProjectForm(initial={'projectname': project.projectname,
                                          'description': project.description,
                                          'manager': manager
                                         })

    for user in users:
        project_role = [str(role.role) for role in
                nova.get_user_roles(user.memberId, project_name)]
        global_role = [str(role.role) for role in
                nova.get_user_roles(user.memberId, project=False)]

        user.project_roles = ", ".join(project_role)
        user.global_roles = ", ".join(global_role)

    return render_to_response(
        'admin/django_openstack/nova/project/edit_project.html',
        {'project': project,
         'users': users,
         'form': form},
        context_instance=template.RequestContext(request))


@staff_member_required
def add_project(request):
    nova = get_nova_admin_connection()

    if request.method == 'POST':
        form = forms.ProjectForm(request.POST)
        if form.is_valid():
            manager = form.cleaned_data['manager']
            nova.create_project(form.cleaned_data['projectname'],
                                manager.username,
                                form.cleaned_data['description'])
            LOG.info('Project "%s" created' %
                        form.cleaned_data['projectname'])
            return redirect('admin_project', request.POST['projectname'])
    else:
        form = forms.ProjectForm()

    return render_to_response(
        'admin/django_openstack/nova/project/add_project.html',
        {'form': form},
        context_instance=template.RequestContext(request))


@staff_member_required
def delete_project(request, project_name):
    nova = get_nova_admin_connection()

    if request.method == 'POST':
        nova.delete_project(project_name)
        LOG.info('Project "%s" deleted' % project_name)
        return redirect('admin_projects')

    project = nova.get_project(project_name)

    return render_to_response(
        'admin/django_openstack/nova/project/delete_project.html',
        {'project': project},
        context_instance=template.RequestContext(request))


def remove_project_roles(username, project):
    nova = get_nova_admin_connection()
    userroles = nova.get_user_roles(username,  project)
    roles = [str(role.role) for role in userroles]

    for role in roles:
        if role == "developer":
            nova.remove_user_role(username, "developer", project)
        if role == "sysadmin":
            nova.remove_user_role(username, "sysadmin", project)
        if role == "netadmin":
            nova.remove_user_role(username, "netadmin", project)

    LOG.info('Removed roles "%s" from user "%s" on project "%s"' %
                (",".join(roles), username, project))


def remove_global_roles(username):
    nova = get_nova_admin_connection()
    userroles = nova.get_user_roles(username)
    roles = [str(role.role) for role in userroles]

    for role in roles:
        if role == "developer":
            nova.remove_user_role(username, "developer")
        if role == "sysadmin":
            nova.remove_user_role(username, "sysadmin")
        if role == "netadmin":
            nova.remove_user_role(username, "netadmin")
        if role == "cloudadmin":
            nova.remove_user_role(username, "cloudadmin")
        if role == "itsec":
            nova.remove_user_role(username, "itsec")

    LOG.info('Removed global roles "%s" from user "%s"' %
             (",".join(roles), username))


@staff_member_required
def project_user(request, project_name, project_user):
    nova = get_nova_admin_connection()
    project = nova.get_project(project_name)
    userroles = nova.get_user_roles(project_user, project_name)

    try:
        modeluser = auth_models.User.objects.get(username=project_user)
    except auth_models.User.DoesNotExist:
        modeluser = None

    if request.method == 'POST':
        form = forms.ProjectUserForm(project, request.user, request.POST)
        if form.is_valid():
            username = project_user

            # hacky work around to interface correctly with
            # multiple select form
            remove_project_roles(username, project_name)

            roleform = request.POST.getlist("role")
            for role in roleform:
                nova.add_user_role(username, str(role), project_name)

            LOG.info('Added roles "%s" to user "%s" on project "%s"' %
                        ",".join(str(role) for role in roleform),
                        username, project_name)

            return redirect('admin_project', project_name)
    else:
        roles = [str(role.role) for role in userroles]
        form = forms.ProjectUserForm(project,
                                     request.user,
                                     {'role': roles,
                                      'user': modeluser})

    return render_to_response(
        'admin/django_openstack/nova/project/project_user.html',
        {'form': form,
         'project': project,
         'user': modeluser},
        context_instance=template.RequestContext(request))


@staff_member_required
def add_project_user(request, project_name):
    nova = get_nova_admin_connection()

    if request.method == 'POST':
        form = forms.AddProjectUserForm(request.POST, project=project_name)
        if form.is_valid():
            username = form.cleaned_data["username"].username
            roleform = request.POST.getlist("role")

            nova.add_project_member(username, project_name,)

            for role in roleform:
                nova.add_user_role(username, str(role), project_name)

            LOG.info('Added user "%s" to project "%s" with roles "%s"' %
                        (username, project_name,
                        ",".join(str(role) for role in roleform)))

            return redirect('admin_project', project_name)
    else:
        form = forms.AddProjectUserForm(project=project_name)

    project = nova.get_project(project_name)

    return render_to_response(
        'admin/django_openstack/nova/project/add_project_user.html',
        {'form': form,
         'project': project},
        context_instance=template.RequestContext(request))


@staff_member_required
def delete_project_user(request, project_name, project_user):
    nova = get_nova_admin_connection()

    if request.method == 'POST':
        nova.remove_project_member(project_user, project_name)
        return redirect('admin_project', project_name)

    project = nova.get_project(project_name)
    user = nova.get_user(project_user)

    return render_to_response(
        'admin/django_openstack/nova/project/delete_project_user.html',
        {'user': user,
         'project': project},
        context_instance=template.RequestContext(request))


@staff_member_required
def users_list(request):
    nova = get_nova_admin_connection()
    users = nova.get_users()

    for user in users:
        # NOTE(devcamcar): Temporarily disabled for performance reasons.
        #roles = [str(role.role) for role in
        #         nova.get_user_roles(user.username)]
        roles = []
        user.roles = ", ".join(roles)

    return render_to_response(
        'admin/django_openstack/nova/project/user_list.html',
        {'users': users},
        context_instance=template.RequestContext(request))


@staff_member_required
def user_roles(request, user_id):
    nova = get_nova_admin_connection()
    userroles = nova.get_user_roles(user_id)
    try:
        modeluser = auth_models.User.objects.get(username=user_id)
    except auth_models.User.DoesNotExist:
        modeluser = None

    if request.method == 'POST':
        form = forms.GlobalRolesForm(request.POST)
        if form.is_valid():
            username = user_id

            # hacky work around to interface correctly with
            # multiple select form
            remove_global_roles(username)

            roleform = request.POST.getlist("role")
            for role in roleform:
                nova.add_user_role(username, str(role))

            LOG.info('Added user "%s" to global roles "%s"' %
                     (username, ",".join(str(role) for role in roleform)))

            return redirect('admin_user_roles', user_id)
    else:
        roles = [str(role.role) for role in userroles]
        form = forms.GlobalRolesForm({
            'username': modeluser and modeluser.id or None,
            'role': roles,
        })

    return render_to_response(
        'admin/django_openstack/nova/project/global_edit_user.html',
        {'form': form,
         'user': modeluser},
        context_instance=template.RequestContext(request))
