# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2013 NTT MCL, Inc.
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

from openstack_dashboard.dashboards.project.network_topology import views


urlpatterns = patterns(
    'openstack_dashboard.dashboards.project.network_topology.views',
    url(r'^$', views.NetworkTopologyView.as_view(), name='index'),
    url(r'^router$', views.RouterView.as_view(), name='router'),
    url(r'^instance$', views.InstanceView.as_view(), name='instance'),
    url(r'^router/(?P<router_id>[^/]+)/$', views.RouterDetailView.as_view(),
        name='detail'),
    url(r'^json$', views.JSONView.as_view(), name='json'),
    url(r'^launchinstance$', views.NTLaunchInstanceView.as_view(),
        name='launchinstance'),
    url(r'^createnetwork$', views.NTCreateNetworkView.as_view(),
        name='createnetwork'),
    url(r'^createrouter$', views.NTCreateRouterView.as_view(),
        name='createrouter'),
)
