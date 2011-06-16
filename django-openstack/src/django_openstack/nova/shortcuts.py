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
Helper methods for commonly used operations.
"""

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.translation import ugettext as _

from django_openstack.core.connection import get_nova_admin_connection
from django_openstack.nova import manager
from django_openstack.nova.exceptions import wrap_nova_error


@wrap_nova_error
def get_project_or_404(request, project_id):
    """
    Returns a project or 404s if it doesn't exist.
    """

    # Ensure that a connection is never attempted for a
    # user that is unauthenticated.
    if not request.user.is_authenticated:
        raise PermissionDenied(_('User not authenticated'))

    nova = get_nova_admin_connection()
    project = nova.get_project(project_id)
    region = get_current_region(request)

    if not project:
        raise Http404(_('Project %s does not exist.') % project_id)

    return manager.ProjectManager(request.user, project, region)


@wrap_nova_error
def get_projects(user):
    """
    Returns a list of projects for a user.
    """
    #key = 'projects.%s' % user
    #projects = cache.get(key)

    #if not projects:
    #    nova = get_nova_admin_connection()
    #    projects = nova.get_projects(user=user)
    #    cache.set(key, projects, 30)

    #return projects
    nova = get_nova_admin_connection()
    return nova.get_projects(user=user)


@wrap_nova_error
def get_all_regions():
    """
    Returns a list of all regions.
    """
    regions = cache.get('regions')

    if not regions:
        nova = get_nova_admin_connection()
        conn = nova.connection_for(settings.NOVA_ADMIN_USER,
                                   settings.NOVA_PROJECT)
        results = conn.get_all_regions()
        regions = [{'name': r.name, 'endpoint': r.endpoint} for r in results]
        cache.set('regions', regions, 60 * 60 * 24)

    return regions


def get_region(region_name):
    regions = get_all_regions()
    try:
        return [r for r in regions if r['name'] == region_name][0]
    except IndexError:
        return None


def get_current_region(request):
    """
    Returns the currently selected region for a user.
    """
    region_name = request.session.get('region', settings.NOVA_DEFAULT_REGION)
    return get_region(region_name)


def set_current_region(request, region_name):
    """
    Sets the current region selection for a user.
    """
    request.session['region'] = region_name


@wrap_nova_error
def get_user_image_permissions(username, project_name):
    """
    Returns true if user is a sysadmin and can modify image attributes.
    """
    nova = get_nova_admin_connection()
    user_has_modify_permissions = False

    # checks global roles, if user is a sysadmin they can
    # modify image attribtues.
    if not user_has_modify_permissions:
        for role in nova.get_user_roles(username):
            if role.role == "sysadmin":
                user_has_modify_permissions = True

    # checks project roles, if user is a sysadmin they can
    # modify image attribtues.
    if not user_has_modify_permissions:
        for role in nova.get_user_roles(username, project_name):
            if role.role == "sysadmin":
                user_has_modify_permissions = True

    return user_has_modify_permissions
