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

from openstack_dashboard.dashboards.project.volumes.snapshots import views


urlpatterns = [
    url(r'^(?P<snapshot_id>[^/]+)$',
        views.DetailView.as_view(),
        name='detail'),
    url(r'^(?P<snapshot_id>[^/]+)/update/$',
        views.UpdateView.as_view(),
        name='update'),
]
