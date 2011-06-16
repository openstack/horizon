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
URL patterns for managing Nova projects through the Django admin interface.
"""

from django.conf.urls.defaults import *


#TODO(devcamcar): Standardize url names admin_project_*.

urlpatterns = patterns('',
    url(r'^$',
        'django_openstack.nova.views.admin.projects_list',
        name='admin_projects'),
    url(r'^add/$',
        'django_openstack.nova.views.admin.add_project',
        name='add_project'),
    url(r'^(?P<project_name>[^/]+)/$',
        'django_openstack.nova.views.admin.project_view',
        name='admin_project'),
    url(r'^(?P<project_name>[^/]+)/user/(?P<project_user>[^/]+)/delete/',
        'django_openstack.nova.views.admin.delete_project_user',
        name='admin_project_delete_user'),
    url(r'^(?P<project_name>[^/]+)/delete/$',
        'django_openstack.nova.views.admin.delete_project',
        name='delete_project'),
    url(r'^(?P<project_name>[^/]+)/user/add/$',
        'django_openstack.nova.views.admin.add_project_user',
        name='add_project_user'),
    url(r'^(?P<project_name>[^/]+)/user/(?P<project_user>[^/]+)/$',
        'django_openstack.nova.views.admin.project_user',
        name='project_user'),
    url(r'^(?P<project_id>[^/]+)/sendcredentials/$',
        'django_openstack.nova.views.admin.project_sendcredentials',
        name='admin_project_sendcredentials'),
    url(r'^(?P<project_id>[^/]+)/start_vpn/$',
        'django_openstack.nova.views.admin.project_start_vpn',
        name='admin_project_start_vpn'),
)
