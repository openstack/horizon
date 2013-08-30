# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


from django.conf.urls.defaults import patterns  # noqa
from django.conf.urls.defaults import url  # noqa

from openstack_dashboard.dashboards.project.network_topology.views import\
    InstanceView  # noqa
from openstack_dashboard.dashboards.project.network_topology.views import\
    JSONView  # noqa
from openstack_dashboard.dashboards.project.network_topology.views import\
    NetworkTopologyView  # noqa
from openstack_dashboard.dashboards.project.network_topology.views import\
    NTCreateNetworkView  # noqa
from openstack_dashboard.dashboards.project.network_topology.views import\
    NTCreateRouterView  # noqa
from openstack_dashboard.dashboards.project.network_topology.views import\
    NTLaunchInstanceView  # noqa
from openstack_dashboard.dashboards.project.network_topology.views import\
    RouterDetailView  # noqa
from openstack_dashboard.dashboards.project.network_topology.views import\
    RouterView  # noqa


urlpatterns = patterns(
    'openstack_dashboard.dashboards.project.network_topology.views',
    url(r'^$', NetworkTopologyView.as_view(), name='index'),
    url(r'^router$', RouterView.as_view(), name='router'),
    url(r'^instance$', InstanceView.as_view(), name='instance'),
    url(r'^router/(?P<router_id>[^/]+)/$', RouterDetailView.as_view(),
        name='detail'),
    url(r'^json$', JSONView.as_view(), name='json'),
    url(r'^launchinstance$', NTLaunchInstanceView.as_view(),
        name='launchinstance'),
    url(r'^createnetwork$', NTCreateNetworkView.as_view(),
        name='createnetwork'),
    url(r'^createrouter$', NTCreateRouterView.as_view(),
        name='createrouter'),
)
