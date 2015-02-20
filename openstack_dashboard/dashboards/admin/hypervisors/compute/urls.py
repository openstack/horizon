# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.admin.hypervisors.compute import views


urlpatterns = patterns(
    'openstack_dashboard.dashboards.admin.hypervisors.compute.views',
    url(r'^(?P<compute_host>[^/]+)/evacuate_host$',
        views.EvacuateHostView.as_view(),
        name='evacuate_host'),
    url(r'^(?P<compute_host>[^/]+)/disable_service$',
        views.DisableServiceView.as_view(),
        name='disable_service'),
    url(r'^(?P<compute_host>[^/]+)/migrate_host$',
        views.MigrateHostView.as_view(),
        name='migrate_host'),
)
