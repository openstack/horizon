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

from django.urls import re_path

from openstack_dashboard.dashboards.admin.instances import views


INSTANCES = r'^(?P<instance_id>[^/]+)/%s$'


urlpatterns = [
    re_path(r'^$', views.AdminIndexView.as_view(), name='index'),
    re_path(INSTANCES % 'update', views.AdminUpdateView.as_view(),
            name='update'),
    re_path(INSTANCES % 'detail', views.DetailView.as_view(), name='detail'),
    re_path(INSTANCES % 'console', views.console, name='console'),
    re_path(INSTANCES % 'vnc', views.vnc, name='vnc'),
    re_path(INSTANCES % 'mks', views.mks, name='mks'),
    re_path(INSTANCES % 'spice', views.spice, name='spice'),
    re_path(INSTANCES % 'rdp', views.rdp, name='rdp'),
    re_path(INSTANCES % 'live_migrate', views.LiveMigrateView.as_view(),
            name='live_migrate'),
    re_path(INSTANCES % 'rescue', views.RescueView.as_view(), name='rescue'),
]
