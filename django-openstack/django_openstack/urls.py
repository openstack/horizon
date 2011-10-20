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

from django.conf.urls.defaults import patterns, url, include
from django.conf import settings
from django_openstack.signals import *
from django.views.generic import TemplateView

urlpatterns = patterns('',
    url(r'^auth/', include('django_openstack.auth.urls')),
    url(r'^dash/', include('django_openstack.dash.urls')),
    url(r'^syspanel/', include('django_openstack.syspanel.urls')),
    url(r'^settings/$', TemplateView.as_view(
                template_name='django_openstack/dash/settings.html'),
                name='dashboard_settings')

)

# import urls from modules
for module_urls in dash_modules_urls.send(sender=dash_modules_urls):
    urlpatterns += module_urls[1].urlpatterns
