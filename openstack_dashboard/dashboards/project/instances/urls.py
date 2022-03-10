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

from openstack_dashboard.dashboards.project.instances import views


INSTANCES = r'^(?P<instance_id>[^/]+)/%s$'
INSTANCES_KEYPAIR = r'^(?P<instance_id>[^/]+)/(?P<keypair_name>[^/]+)/%s$'

urlpatterns = [
    re_path(r'^$', views.IndexView.as_view(), name='index'),
    re_path(r'^(?P<instance_id>[^/]+)/$',
            views.DetailView.as_view(), name='detail'),
    re_path(INSTANCES % 'update', views.UpdateView.as_view(), name='update'),
    re_path(INSTANCES % 'rebuild', views.RebuildView.as_view(), name='rebuild'),
    re_path(INSTANCES % 'serial', views.SerialConsoleView.as_view(),
            name='serial'),
    re_path(INSTANCES % 'console', views.console, name='console'),
    re_path(INSTANCES % 'auto_console',
            views.auto_console, name='auto_console'),
    re_path(INSTANCES % 'vnc', views.vnc, name='vnc'),
    re_path(INSTANCES % 'spice', views.spice, name='spice'),
    re_path(INSTANCES % 'rdp', views.rdp, name='rdp'),
    re_path(INSTANCES % 'resize', views.ResizeView.as_view(), name='resize'),
    re_path(INSTANCES_KEYPAIR % 'decryptpassword',
            views.DecryptPasswordView.as_view(), name='decryptpassword'),
    re_path(INSTANCES % 'disassociate',
            views.DisassociateView.as_view(), name='disassociate'),
    re_path(INSTANCES % 'attach_interface',
            views.AttachInterfaceView.as_view(), name='attach_interface'),
    re_path(INSTANCES % 'detach_interface',
            views.DetachInterfaceView.as_view(), name='detach_interface'),
    re_path(r'^(?P<instance_id>[^/]+)/attach_volume/$',
            views.AttachVolumeView.as_view(),
            name='attach_volume'),
    re_path(r'^(?P<instance_id>[^/]+)/detach_volume/$',
            views.DetachVolumeView.as_view(),
            name='detach_volume'),
    re_path(r'^(?P<instance_id>[^/]+)/ports/(?P<port_id>[^/]+)/update$',
            views.UpdatePortView.as_view(), name='update_port'),
    re_path(INSTANCES % 'rescue', views.RescueView.as_view(), name='rescue'),
]
