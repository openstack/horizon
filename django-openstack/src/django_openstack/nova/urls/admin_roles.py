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
URL patterns for managing Nova user roles through the Django admin interface.
"""

from django.conf.urls.defaults import *


urlpatterns = patterns('',
    url(r'^(?P<user_id>[^/]+)/$',
        'django_openstack.nova.views.admin.user_roles',
        name='admin_user_roles'),
    url(r'^$',
        'django_openstack.nova.views.admin.users_list',
        name='admin_users_list'),
)
