# Copyright 2019 NEC Corporation
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

from openstack_dashboard.dashboards.admin.volume_groups import views


urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<group_id>[^/]+)$',
        views.DetailView.as_view(),
        name='detail'),
    url(r'^(?P<group_id>[^/]+)/remove_volumese/$',
        views.RemoveVolumesView.as_view(),
        name='remove_volumes'),
    url(r'^(?P<group_id>[^/]+)/delete/$',
        views.DeleteView.as_view(),
        name='delete'),
    url(r'^(?P<group_id>[^/]+)/manage/$',
        views.ManageView.as_view(),
        name='manage'),
]
