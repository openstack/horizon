# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

from django.conf import settings
from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.project.containers import views


VIEW_MOD = 'openstack_dashboard.dashboards.project.containers.views'

if settings.HORIZON_CONFIG['swift_panel'] == 'angular':
    # New angular containers and objects
    urlpatterns = [
        url(r'^container/((?P<container_name>.+?)/)?'
            '(?P<subfolder_path>(.+/)+)?$',
            views.NgIndexView.as_view(), name='index'),
        url(r'^$',
            views.NgIndexView.as_view(), name='index')
    ]
else:
    # Legacy swift containers and objects
    urlpatterns = patterns(
        VIEW_MOD,
        url(r'^((?P<container_name>.+?)/)?(?P<subfolder_path>(.+/)+)?$',
            views.ContainerView.as_view(), name='index'),

        url(r'^(?P<container_name>(.+/)+)?create$',
            views.CreateView.as_view(),
            name='create'),

        url(r'^(?P<container_name>.+?)/(?P<subfolder_path>(.+/)+)'
            '?container_detail$',
            views.ContainerDetailView.as_view(),
            name='container_detail'),

        url(r'^(?P<container_name>[^/]+)/(?P<object_path>.+)/object_detail$',
            views.ObjectDetailView.as_view(),
            name='object_detail'),

        url(r'^(?P<container_name>[^/]+)/(?P<subfolder_path>(.+/)+)?'
            '(?P<object_name>.+)/update$',
            views.UpdateObjectView.as_view(),
            name='object_update'),

        url(r'^(?P<container_name>.+?)/(?P<subfolder_path>(.+/)+)?upload$',
            views.UploadView.as_view(),
            name='object_upload'),

        url(r'^(?P<container_name>.+?)/(?P<subfolder_path>(.+/)+)'
            '?create_pseudo_folder',
            views.CreatePseudoFolderView.as_view(),
            name='create_pseudo_folder'),

        url(r'^(?P<container_name>[^/]+)/'
            r'(?P<subfolder_path>(.+/)+)?'
            r'(?P<object_name>.+)/copy$',
            views.CopyView.as_view(),
            name='object_copy'),

        url(r'^(?P<container_name>[^/]+)/(?P<object_path>.+)/download$',
            'object_download',
            name='object_download'),
    )
