# Copyright 2012 NEC Corporation
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

from django.conf.urls import include
from django.urls import re_path

from openstack_dashboard.dashboards.project.networks.ports \
    import urls as port_urls
from openstack_dashboard.dashboards.project.networks.ports \
    import views as port_views
from openstack_dashboard.dashboards.project.networks.subnets \
    import urls as subnet_urls
from openstack_dashboard.dashboards.project.networks.subnets \
    import views as subnet_views
from openstack_dashboard.dashboards.project.networks import views


NETWORKS = r'^(?P<network_id>[^/]+)/%s$'


urlpatterns = [
    re_path(r'^$', views.IndexView.as_view(), name='index'),
    re_path(r'^create$', views.CreateView.as_view(), name='create'),
    re_path(NETWORKS % r'detail(\?tab=network_tabs__overview)?$',
            views.DetailView.as_view(),
            name='detail'),
    re_path(NETWORKS % r'detail\?tab=network_tabs__ports_tab$',
            views.DetailView.as_view(), name='ports_tab'),
    re_path(NETWORKS % r'detail\?tab=network_tabs__subnets_tab$',
            views.DetailView.as_view(), name='subnets_tab'),
    re_path(NETWORKS % 'update', views.UpdateView.as_view(), name='update'),
    re_path(NETWORKS % 'subnets/create', subnet_views.CreateView.as_view(),
            name='createsubnet'),
    re_path(NETWORKS % 'ports/create',
            port_views.CreateView.as_view(), name='addport'),
    re_path(r'^(?P<network_id>[^/]+)/subnets/(?P<subnet_id>[^/]+)/update$',
            subnet_views.UpdateView.as_view(), name='editsubnet'),
    re_path(r'^(?P<network_id>[^/]+)/ports/(?P<port_id>[^/]+)/update$',
            port_views.UpdateView.as_view(), name='editport'),
    re_path(r'^subnets/', include((subnet_urls, 'subnets'))),
    re_path(r'^ports/', include((port_urls, 'ports'))),
]
