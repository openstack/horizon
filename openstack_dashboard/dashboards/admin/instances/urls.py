# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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

from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.admin.instances import views


INSTANCES = r'^(?P<instance_id>[^/]+)/%s$'


urlpatterns = patterns(
    'openstack_dashboard.dashboards.admin.instances.views',
    url(r'^$', views.AdminIndexView.as_view(), name='index'),
    url(INSTANCES % 'update', views.AdminUpdateView.as_view(), name='update'),
    url(INSTANCES % 'detail', views.DetailView.as_view(), name='detail'),
    url(INSTANCES % 'console', 'console', name='console'),
    url(INSTANCES % 'vnc', 'vnc', name='vnc'),
    url(INSTANCES % 'spice', 'spice', name='spice'),
    url(INSTANCES % 'rdp', 'rdp', name='rdp'),
    url(INSTANCES % 'live_migrate', views.LiveMigrateView.as_view(),
        name='live_migrate'),
)
