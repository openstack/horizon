# Copyright 2012 Nebula, Inc.
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
from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.project.volumes.backups \
    import urls as backups_urls
from openstack_dashboard.dashboards.project.volumes.cgroups \
    import urls as cgroup_urls
from openstack_dashboard.dashboards.project.volumes.snapshots \
    import urls as snapshot_urls
from openstack_dashboard.dashboards.project.volumes import views
from openstack_dashboard.dashboards.project.volumes.volumes \
    import urls as volume_urls

urlpatterns = patterns(
    '',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^\?tab=volumes_and_snapshots__snapshots_tab$',
        views.IndexView.as_view(), name='snapshots_tab'),
    url(r'^\?tab=volumes_and_snapshots__volumes_tab$',
        views.IndexView.as_view(), name='volumes_tab'),
    url(r'^\?tab=volumes_and_snapshots__backups_tab$',
        views.IndexView.as_view(), name='backups_tab'),
    url(r'^\?tab=volumes_and_snapshots__cgroups_tab$',
        views.IndexView.as_view(), name='cgroups_tab'),
    url(r'', include(volume_urls, namespace='volumes')),
    url(r'backups/', include(backups_urls, namespace='backups')),
    url(r'snapshots/', include(snapshot_urls, namespace='snapshots')),
    url(r'cgroups/', include(cgroup_urls, namespace='cgroups')),
)
