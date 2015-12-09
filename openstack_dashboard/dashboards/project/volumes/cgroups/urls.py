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

from openstack_dashboard.dashboards.project.volumes.cgroups import views


urlpatterns = patterns(
    '',
    url(r'^create/$',
        views.CreateView.as_view(),
        name='create'),
    url(r'^(?P<cgroup_id>[^/]+)/update/$',
        views.UpdateView.as_view(),
        name='update'),
    url(r'^(?P<cgroup_id>[^/]+)/manage/$',
        views.ManageView.as_view(),
        name='manage'),
    url(r'^(?P<cgroup_id>[^/]+)$',
        views.DetailView.as_view(),
        name='detail'),
)
