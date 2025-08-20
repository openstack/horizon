# Copyright 2013 B1 Systems GmbH
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
from django.urls import re_path, path
from . import views
from openstack_dashboard.dashboards.admin.hypervisors.compute import urls as compute_urls


urlpatterns = [
    re_path(r'^(?P<hypervisor>[^/]+)/$',
            views.AdminDetailView.as_view(),
            name='detail'),
    re_path(r'^$', views.AdminIndexView.as_view(), name='index'),
    re_path(r'', include((compute_urls, 'compute'))),
    path(
        "open_host_app/<path:host>/",
        views.OpenHostAppView.as_view(),
        name="open_host_app",
    ),
]
