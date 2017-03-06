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

from openstack_dashboard.dashboards.project.backups import views


urlpatterns = [
    url(r'^$', views.BackupsView.as_view(), name='index'),
    url(r'^(?P<backup_id>[^/]+)/$',
        views.BackupDetailView.as_view(),
        name='detail'),
    url(r'^(?P<backup_id>[^/]+)/restore/$',
        views.RestoreBackupView.as_view(),
        name='restore'),
]
