# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.conf.urls import url

from openstack_dashboard.dashboards.admin.volumes import views


urlpatterns = [
    url(r'^$',
        views.VolumesView.as_view(),
        name='index'),
    url(r'^manage/$',
        views.ManageVolumeView.as_view(),
        name='manage'),
    url(r'^(?P<volume_id>[^/]+)/$',
        views.DetailView.as_view(),
        name='detail'),
    url(r'^(?P<volume_id>[^/]+)/update_status$',
        views.UpdateStatusView.as_view(),
        name='update_status'),
    url(r'^(?P<volume_id>[^/]+)/unmanage$',
        views.UnmanageVolumeView.as_view(),
        name='unmanage'),
    url(r'^(?P<volume_id>[^/]+)/migrate$',
        views.MigrateVolumeView.as_view(),
        name='migrate'),
]
