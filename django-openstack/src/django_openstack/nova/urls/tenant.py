# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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

"""
URL patterns for managing Nova projects.
"""

from django.conf.urls.defaults import *


urlpatterns = patterns('',
    url(r'^(?P<tenant_id>[^/]+)/$',
        'django_openstack.nova.views.tenants.detail',
        name='nova_tenant'),
    #url(r'^(?P<project_id>[^/]+)/manage/(?P<username>[^/]+)/',
    #    'django_openstack.nova.views.projects.edit_user',
    #    name='nova_project_edit_user'),
    #url(r'^(?P<project_id>[^/]+)/manage$',
    #    'django_openstack.nova.views.projects.manage',
    #    name='nova_project_manage'),

    # images
    url(r'^(?P<tenant_id>[^/]+)/images$',
        'django_openstack.nova.views.images.index',
        name='nova_images'),
    url(r'^(?P<tenant_id>[^/]+)/images/(?P<image_id>[^/]+)/launch$',
        'django_openstack.nova.views.images.launch',
        name='nova_images_launch'),
    url(r'^(?P<tenant_id>[^/]+)/images/(?P<image_id>[^/]+)/remove$',
        'django_openstack.nova.views.images.remove',
        name='nova_images_remove'),
    url(r'^(?P<tenant_id>[^/]+)/images/(?P<image_id>[^/]+)/update$',
        'django_openstack.nova.views.images.update',
        name='nova_images_update'),
    url(r'^(?P<tenant_id>[^/]+)/images/(?P<image_id>[^/]+)/detail$',
        'django_openstack.nova.views.images.detail',
        name='nova_images_detail'),
    url(r'^(?P<tenant_id>[^/]+)/images/(?P<image_id>[^/]+)$',
        'django_openstack.nova.views.images.privacy',
        name='nova_images_privacy'),

    # instances
    url(r'^(?P<tenant_id>[^/]+)/instances$',
        'django_openstack.nova.views.instances.index',
        name='nova_instances'),
    url(r'^(?P<tenant_id>[^/]+)/instances/refresh$',
        'django_openstack.nova.views.instances.refresh',
        name='nova_instances_refresh'),
    url(r'^(?P<tenant_id>[^/]+)/instances/(?P<instance_id>[^/]+)/refresh$',
        'django_openstack.nova.views.instances.refresh_detail',
        name='nova_instances_refresh_detail'),
    url(r'^(?P<tenant_id>[^/]+)/instances/terminate$',
        'django_openstack.nova.views.instances.terminate',
        name='nova_instances_terminate'),
    url(r'^(?P<tenant_id>[^/]+)/instances/(?P<instance_id>[^/]+)$',
        'django_openstack.nova.views.instances.detail',
        name='nova_instances_detail'),
    url(r'^(?P<tenant_id>[^/]+)/instances/(?P<instance_id>[^/]+)/performance$',
        'django_openstack.nova.views.instances.performance',
        name='nova_instances_performance'),
    url(r'^(?P<tenant_id>[^/]+)/instances/(?P<instance_id>[^/]+)/console$',
        'django_openstack.nova.views.instances.console',
        name='nova_instances_console'),
    url(r'^(?P<tenant_id>[^/]+)/instances/(?P<instance_id>[^/]+)/vnc$',
        'django_openstack.nova.views.instances.vnc',
        name='nova_instances_vnc'),
    url(r'^(?P<tenant_id>[^/]+)/instances/(?P<instance_id>.*)/update$',
        'django_openstack.nova.views.instances.update',
        name='nova_instance_update'),
    url(r'^(?P<tenant_id>[^/]+)/instances/(?P<instance_id>[^/]+)/graph/(?P<graph_name>[^/]+)$',
        'django_openstack.nova.views.instances.graph',
        name='nova_instances_graph'),

    # volumes
    #url(r'^(?P<tenant_id>[^/]+)/volumes/$',
    #    'django_openstack.nova.views.volumes.index',
    #    name='nova_volumes'),
    #url(r'^(?P<tenant_id>[^/]+)/volumes/add$',
    #    'django_openstack.nova.views.volumes.add',
    #    name='nova_volumes_add'),
    #url(r'^(?P<tenant_id>[^/]+)/volumes/attach$',
    #    'django_openstack.nova.views.volumes.attach',
    #    name='nova_volumes_attach'),
    #url(r'^(?P<tenant_id>[^/]+)/volumes/(?P<volume_id>[^/]+)/detach$',
    #    'django_openstack.nova.views.volumes.detach',
    #    name='nova_volumes_detach'),
    #url(r'^(?P<tenant_id>[^/]+)/volumes/(?P<volume_id>[^/]+)/delete$',
    #    'django_openstack.nova.views.volumes.delete',
    #    name='nova_volumes_delete'),
)
