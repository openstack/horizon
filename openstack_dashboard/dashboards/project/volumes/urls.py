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

from django.conf.urls import url

from openstack_dashboard.dashboards.project.backups \
    import views as backup_views
from openstack_dashboard.dashboards.project.volumes import views

urlpatterns = [
    url(r'^$', views.VolumesView.as_view(), name='index'),
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(r'^(?P<volume_id>[^/]+)/extend/$',
        views.ExtendView.as_view(),
        name='extend'),
    url(r'^(?P<volume_id>[^/]+)/attach/$',
        views.EditAttachmentsView.as_view(),
        name='attach'),
    url(r'^(?P<volume_id>[^/]+)/create_snapshot/$',
        views.CreateSnapshotView.as_view(),
        name='create_snapshot'),
    url(r'^(?P<volume_id>[^/]+)/create_transfer/$',
        views.CreateTransferView.as_view(),
        name='create_transfer'),
    url(r'^accept_transfer/$',
        views.AcceptTransferView.as_view(),
        name='accept_transfer'),
    url(r'^(?P<transfer_id>[^/]+)/auth/(?P<auth_key>[^/]+)/$',
        views.ShowTransferView.as_view(),
        name='show_transfer'),
    url(r'^(?P<volume_id>[^/]+)/create_backup/$',
        backup_views.CreateBackupView.as_view(),
        name='create_backup'),
    url(r'^(?P<volume_id>[^/]+)/$',
        views.DetailView.as_view(),
        name='detail'),
    url(r'^(?P<volume_id>[^/]+)/\?tab=volume_details__snapshots_tab$',
        views.DetailView.as_view(),
        name='snapshots_tab'),
    url(r'^(?P<volume_id>[^/]+)/upload_to_image/$',
        views.UploadToImageView.as_view(),
        name='upload_to_image'),
    url(r'^(?P<volume_id>[^/]+)/update/$',
        views.UpdateView.as_view(),
        name='update'),
    url(r'^(?P<volume_id>[^/]+)/retype/$',
        views.RetypeView.as_view(),
        name='retype'),
    url(r'^(?P<volume_id>[^/]+)/encryption_detail/$',
        views.EncryptionDetailView.as_view(),
        name='encryption_detail'),
    url(r'^(?P<transfer_id>[^/]+)/download_creds/(?P<auth_key>[^/]+)$',
        views.DownloadTransferCreds.as_view(),
        name='download_transfer_creds'),
]
