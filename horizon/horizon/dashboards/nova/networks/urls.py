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

from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('horizon.dashboards.nova.networks.views',
    url(r'^$', 'index', name='index'),
    url(r'^create/$', 'create', name='create'),
    url(r'^(?P<network_id>[^/]+)/detail/$', 'detail', name='detail'),
    url(r'^(?P<network_id>[^/]+)/rename/$', 'rename', name='rename'),
    url(r'^(?P<network_id>[^/]+)/ports/create/$', 'port_create',
        name='port_create'),
    url(r'^(?P<network_id>[^/]+)/ports/(?P<port_id>[^/]+)/attach/$',
        'port_attach', name='port_attach'))
