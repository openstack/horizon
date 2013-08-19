# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url

from openstack_dashboard.dashboards.project.containers.views import \
    ContainerDetailView
from openstack_dashboard.dashboards.project.containers.views import \
    ContainerView
from openstack_dashboard.dashboards.project.containers.views import CopyView
from openstack_dashboard.dashboards.project.containers.views import CreateView
from openstack_dashboard.dashboards.project.containers.views import \
    ObjectDetailView
from openstack_dashboard.dashboards.project.containers.views import UploadView


VIEW_MOD = 'openstack_dashboard.dashboards.project.containers.views'

# Swift containers and objects.
urlpatterns = patterns(VIEW_MOD,
    url(r'^((?P<container_name>.+?)/)?(?P<subfolder_path>(.+/)+)?$',
        ContainerView.as_view(), name='index'),

    url(r'^(?P<container_name>(.+/)+)?create$',
        CreateView.as_view(),
        name='create'),

    url(r'^(?P<container_name>.+?)/(?P<subfolder_path>(.+/)+)'
            '?container_detail$',
        ContainerDetailView.as_view(),
        name='container_detail'),

    url(r'^(?P<container_name>[^/]+)/(?P<object_path>.+)/object_detail$',
        ObjectDetailView.as_view(),
        name='object_detail'),

    url(r'^(?P<container_name>.+?)/(?P<subfolder_path>(.+/)+)?upload$',
        UploadView.as_view(),
        name='object_upload'),

    url(r'^(?P<container_name>[^/]+)/'
         r'(?P<subfolder_path>(.+/)+)?'
         r'(?P<object_name>.+)/copy$',
        CopyView.as_view(),
        name='object_copy'),

    url(r'^(?P<container_name>[^/]+)/(?P<object_path>.+)/download$',
        'object_download',
        name='object_download'),
)
