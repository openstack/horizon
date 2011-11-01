# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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

from django.conf.urls.defaults import *

SECURITY_GROUPS = r'^(?P<tenant_id>[^/]+)/security_groups/' \
                   '(?P<security_group_id>[^/]+)/%s$'
INSTANCES = r'^(?P<tenant_id>[^/]+)/instances/(?P<instance_id>[^/]+)/%s$'
IMAGES = r'^(?P<tenant_id>[^/]+)/images/(?P<image_id>[^/]+)/%s$'
KEYPAIRS = r'^(?P<tenant_id>[^/]+)/keypairs/%s$'
SNAPSHOTS = r'^(?P<tenant_id>[^/]+)/snapshots/(?P<instance_id>[^/]+)/%s$'
VOLUMES = r'^(?P<tenant_id>[^/]+)/volumes/(?P<volume_id>[^/]+)/%s$'
CONTAINERS = r'^(?P<tenant_id>[^/]+)/containers/%s$'
FLOATING_IPS = r'^(?P<tenant_id>[^/]+)/floating_ips/(?P<ip_id>[^/]+)/%s$'
OBJECTS = r'^(?P<tenant_id>[^/]+)/containers/(?P<container_name>[^/]+)/%s$'
NETWORKS = r'^(?P<tenant_id>[^/]+)/networks/%s$'
PORTS = r'^(?P<tenant_id>[^/]+)/networks/(?P<network_id>[^/]+)/ports/%s$'

urlpatterns = patterns('django_openstack.dash.views.instances',
    url(r'^(?P<tenant_id>[^/]+)/$', 'usage', name='dash_usage'),
    url(r'^(?P<tenant_id>[^/]+)/instances/$', 'index', name='dash_instances'),
    url(r'^(?P<tenant_id>[^/]+)/instances/refresh$', 'refresh',
        name='dash_instances_refresh'),
    url(INSTANCES % 'detail', 'detail', name='dash_instances_detail'),
    url(INSTANCES % 'console', 'console', name='dash_instances_console'),
    url(INSTANCES % 'vnc', 'vnc', name='dash_instances_vnc'),
    url(INSTANCES % 'update', 'update', name='dash_instances_update'),
)

urlpatterns += patterns('django_openstack.dash.views.security_groups',
    url(r'^(?P<tenant_id>[^/]+)/security_groups/$', 'index',
        name='dash_security_groups'),
    url(r'^(?P<tenant_id>[^/]+)/security_groups/create$', 'create',
        name='dash_security_groups_create'),
    url(SECURITY_GROUPS % 'edit_rules', 'edit_rules',
        name='dash_security_groups_edit_rules'),
)

urlpatterns += patterns('django_openstack.dash.views.images',
    url(r'^(?P<tenant_id>[^/]+)/images/$', 'index', name='dash_images'),
    url(IMAGES % 'launch', 'launch', name='dash_images_launch'),
    url(IMAGES % 'update', 'update', name='dash_images_update'),
)

urlpatterns += patterns('django_openstack.dash.views.keypairs',
    url(r'^(?P<tenant_id>[^/]+)/keypairs/$', 'index', name='dash_keypairs'),
    url(KEYPAIRS % 'create', 'create', name='dash_keypairs_create'),
    url(KEYPAIRS % 'import', 'import_keypair', name='dash_keypairs_import'),
)

urlpatterns += patterns('django_openstack.dash.views.floating_ips',
    url(r'^(?P<tenant_id>[^/]+)/floating_ips/$', 'index',
        name='dash_floating_ips'),
    url(FLOATING_IPS % 'associate', 'associate',
        name='dash_floating_ips_associate'),
    url(FLOATING_IPS % 'disassociate', 'disassociate',
        name='dash_floating_ips_disassociate'),
)

urlpatterns += patterns('django_openstack.dash.views.snapshots',
    url(r'^(?P<tenant_id>[^/]+)/snapshots/$', 'index', name='dash_snapshots'),
    url(SNAPSHOTS % 'create', 'create', name='dash_snapshots_create'),
)

urlpatterns += patterns('django_openstack.dash.views.volumes',
    url(r'^(?P<tenant_id>[^/]+)/volumes/$', 'index', name='dash_volumes'),
    url(r'^(?P<tenant_id>[^/]+)/volumes/create', 'create',
            name='dash_volumes_create'),
    url(VOLUMES % 'attach', 'attach', name='dash_volumes_attach'),
    url(VOLUMES % 'detail', 'detail', name='dash_volumes_detail'),
)

# Swift containers and objects.
urlpatterns += patterns('django_openstack.dash.views.containers',
    url(CONTAINERS % '', 'index', name='dash_containers'),
    url(CONTAINERS % 'create', 'create', name='dash_containers_create'),
)

urlpatterns += patterns('django_openstack.dash.views.objects',
    url(OBJECTS % '', 'index', name='dash_objects'),
    url(OBJECTS % 'upload', 'upload', name='dash_objects_upload'),
    url(OBJECTS % '(?P<object_name>[^/]+)/copy',
        'copy', name='dash_object_copy'),
    url(OBJECTS % '(?P<object_name>[^/]+)/download',
        'download', name='dash_objects_download'),
)

urlpatterns += patterns('django_openstack.dash.views.networks',
    url(r'^(?P<tenant_id>[^/]+)/networks/$', 'index', name='dash_networks'),
    url(NETWORKS % 'create', 'create', name='dash_network_create'),
    url(NETWORKS % '(?P<network_id>[^/]+)/detail', 'detail',
        name='dash_networks_detail'),
    url(NETWORKS % '(?P<network_id>[^/]+)/rename', 'rename',
        name='dash_network_rename'),
)

urlpatterns += patterns('django_openstack.dash.views.ports',
    url(PORTS % 'create', 'create', name='dash_ports_create'),
    url(PORTS % '(?P<port_id>[^/]+)/attach', 'attach',
        name='dash_ports_attach'),
)
