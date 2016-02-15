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

from django.conf.urls import url

from openstack_dashboard.dashboards.project.instances import views


INSTANCES = r'^(?P<instance_id>[^/]+)/%s$'
INSTANCES_KEYPAIR = r'^(?P<instance_id>[^/]+)/(?P<keypair_name>[^/]+)/%s$'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^launch$', views.LaunchInstanceView.as_view(), name='launch'),
    url(r'^(?P<instance_id>[^/]+)/$',
        views.DetailView.as_view(), name='detail'),
    url(INSTANCES % 'update', views.UpdateView.as_view(), name='update'),
    url(INSTANCES % 'rebuild', views.RebuildView.as_view(), name='rebuild'),
    url(INSTANCES % 'serial', views.SerialConsoleView.as_view(),
        name='serial'),
    url(INSTANCES % 'console', views.console, name='console'),
    url(INSTANCES % 'vnc', views.vnc, name='vnc'),
    url(INSTANCES % 'spice', views.spice, name='spice'),
    url(INSTANCES % 'rdp', views.rdp, name='rdp'),
    url(INSTANCES % 'resize', views.ResizeView.as_view(), name='resize'),
    url(INSTANCES_KEYPAIR % 'decryptpassword',
        views.DecryptPasswordView.as_view(), name='decryptpassword'),
    url(INSTANCES % 'attach_interface',
        views.AttachInterfaceView.as_view(), name='attach_interface'),
    url(INSTANCES % 'detach_interface',
        views.DetachInterfaceView.as_view(), name='detach_interface'),
]
