#    (c) Copyright 2014 Hewlett-Packard Development Company, L.P.
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

from django.conf.urls import url  # noqa

from openstack_dashboard.dashboards.admin.metadata_defs import views


NAMESPACES = r'^(?P<namespace_id>[^/]+)/%s$'


urlpatterns = [
    url(r'^$', views.AdminIndexView.as_view(), name='index'),
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(NAMESPACES % 'detail', views.DetailView.as_view(), name='detail'),
    url(r'^(?P<id>[^/]+)/resource_types/$',
        views.ManageResourceTypes.as_view(), name='resource_types'),
]
