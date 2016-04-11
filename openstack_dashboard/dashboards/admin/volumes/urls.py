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

from django.conf.urls import include
from django.conf.urls import url

from openstack_dashboard.dashboards.admin.volumes.snapshots \
    import urls as snapshot_urls
from openstack_dashboard.dashboards.admin.volumes import views
from openstack_dashboard.dashboards.admin.volumes.volume_types \
    import urls as volume_types_urls
from openstack_dashboard.dashboards.admin.volumes.volumes \
    import urls as volumes_urls

urlpatterns = [
    url(r'^$',
        views.IndexView.as_view(),
        name='index'),
    url(r'^\?tab=volumes_group_tabs__snapshots_tab$',
        views.IndexView.as_view(),
        name='snapshots_tab'),
    url(r'^\?tab=volumes_group_tabs__volumes_tab$',
        views.IndexView.as_view(),
        name='volumes_tab'),
    url(r'^\?tab=volumes_group_tabs__volume_types_tab$',
        views.IndexView.as_view(),
        name='volume_types_tab'),
    url(r'',
        include(volumes_urls, namespace='volumes')),
    url(r'volume_types/',
        include(volume_types_urls, namespace='volume_types')),
    url(r'snapshots/',
        include(snapshot_urls, namespace='snapshots')),
]
