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
URL patterns for testing django-openstack views.
"""

from django.conf.urls.defaults import *
from django.conf.urls.defaults import *


urlpatterns = patterns('',
    url(r'^projects/', include('django_openstack.nova.urls.project')),
    url(r'^region/', include('django_openstack.nova.urls.region')),
    url(r'^admin/projects/', include('django_openstack.nova.urls.admin_project')),
    url(r'^admin/roles/', include('django_openstack.nova.urls.admin_roles')),
    url(r'^credentials/download/(?P<auth_token>\w+)/$',
        'django_openstack.nova.views.credentials.authorize_credentials',
        name='nova_credentials_authorize'),
)
