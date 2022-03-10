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

from django.urls import re_path

from openstack_dashboard.dashboards.project.network_topology import views


urlpatterns = [
    re_path(r'^$', views.NetworkTopologyView.as_view(), name='index'),
    re_path(r'^router$', views.RouterView.as_view(), name='router'),
    re_path(r'^network$', views.NetworkView.as_view(), name='network'),
    re_path(r'^instance$', views.InstanceView.as_view(), name='instance'),
    re_path(r'^router/(?P<router_id>[^/]+)/$',
            views.RouterDetailView.as_view(),
            name='detail'),
    re_path(r'^router/(?P<router_id>[^/]+)/addinterface$',
            views.NTAddInterfaceView.as_view(), name='interface'),
    re_path(r'^network/(?P<network_id>[^/]+)/$',
            views.NetworkDetailView.as_view(),
            name='detail'),
    re_path(r'^network/(?P<network_id>[^/]+)/subnet/create$',
            views.NTCreateSubnetView.as_view(), name='subnet'),
    re_path(r'^json$', views.JSONView.as_view(), name='json'),
    re_path(r'^createnetwork$', views.NTCreateNetworkView.as_view(),
            name='createnetwork'),
    re_path(r'^createrouter$', views.NTCreateRouterView.as_view(),
            name='createrouter'),
]
