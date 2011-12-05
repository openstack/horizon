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

INSTANCES = r'^(?P<instance_id>[^/]+)/%s$'

urlpatterns = patterns(
    'horizon.dashboards.nova.instances_and_volumes.instances.views',
    url(r'^$', 'index', name='index'),
    url(r'^usage/$', 'usage', name='usage'),
    url(r'^refresh$', 'refresh', name='refresh'),
    url(INSTANCES % 'detail', 'detail', name='detail'),
    url(INSTANCES % 'console', 'console', name='console'),
    url(INSTANCES % 'vnc', 'vnc', name='vnc'),
    url(INSTANCES % 'update', 'update', name='update'),
)
