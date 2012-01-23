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


urlpatterns = patterns('horizon.views.auth',
    url(r'home/$', 'user_home', name='user_home'),
    url(r'auth/login/$', 'login', name='auth_login'),
    url(r'auth/logout/$', 'logout', name='auth_logout'),
    url(r'auth/switch/(?P<tenant_id>[^/]+)/$', 'switch_tenants',
        name='auth_switch'))

urlpatterns += patterns('',
    url(r'^i18n/', include('django.conf.urls.i18n')))
