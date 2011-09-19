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

"""
URL patterns for testing django-openstack views.
"""

from django.conf.urls.defaults import *

from django_openstack import urls as django_openstack_urls


urlpatterns = patterns('',
    url(r'^$', 'django_openstack.tests.views.fakeView', name='splash'),
    url(r'^dash/$', 'django_openstack.dash.views.instances.usage',
        name='dash_overview'),
    url(r'^syspanel/$', 'django_openstack.syspanel.views.instances.usage',
        name='syspanel_overview')
)


# NOTE(termie): just append them since we want the routes at the root
urlpatterns += django_openstack_urls.urlpatterns
