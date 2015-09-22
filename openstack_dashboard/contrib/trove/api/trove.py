# Copyright 2013 Rackspace Hosting.
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

import logging

from django.conf import settings
from troveclient.v1 import client

from openstack_dashboard.api import base

from horizon.utils import functions as utils
from horizon.utils.memoized import memoized  # noqa

LOG = logging.getLogger(__name__)


@memoized
def troveclient(request):
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    trove_url = base.url_for(request, 'database')
    c = client.Client(request.user.username,
                      request.user.token.id,
                      project_id=request.user.project_id,
                      auth_url=trove_url,
                      insecure=insecure,
                      cacert=cacert,
                      http_log_debug=settings.DEBUG)
    c.client.auth_token = request.user.token.id
    c.client.management_url = trove_url
    return c


def cluster_list(request, marker=None):
    page_size = utils.get_page_size(request)
    return troveclient(request).clusters.list(limit=page_size, marker=marker)


def cluster_get(request, cluster_id):
    return troveclient(request).clusters.get(cluster_id)


def cluster_delete(request, cluster_id):
    return troveclient(request).clusters.delete(cluster_id)


def cluster_create(request, name, volume, flavor, num_instances,
                   datastore, datastore_version,
                   nics=None, root_password=None):
    # TODO(dklyle): adding to support trove without volume
    # support for now until API supports checking for volume support
    if volume > 0:
        volume_params = {'size': volume}
    else:
        volume_params = None
    instances = []
    for i in range(num_instances):
        instance = {}
        instance["flavorRef"] = flavor
        instance["volume"] = volume_params
        if nics:
            instance["nics"] = [{"net-id": nics}]
        instances.append(instance)

    # TODO(saurabhs): vertica needs root password on cluster create
    return troveclient(request).clusters.create(
        name,
        datastore,
        datastore_version,
        instances=instances)


def cluster_add_shard(request, cluster_id):
    return troveclient(request).clusters.add_shard(cluster_id)


def create_cluster_root(request, cluster_id, password):
    # It appears the code below depends on this trove change
    # https://review.openstack.org/#/c/166954/.  Comment out when that
    # change merges.
    # return troveclient(request).cluster.reset_root_password(cluster_id)
    troveclient(request).root.create_cluster_root(cluster_id, password)


def instance_list(request, marker=None):
    page_size = utils.get_page_size(request)
    return troveclient(request).instances.list(limit=page_size, marker=marker)


def instance_get(request, instance_id):
    return troveclient(request).instances.get(instance_id)


def instance_delete(request, instance_id):
    return troveclient(request).instances.delete(instance_id)


def instance_create(request, name, volume, flavor, databases=None,
                    users=None, restore_point=None, nics=None,
                    datastore=None, datastore_version=None,
                    replica_of=None):
    # TODO(dklyle): adding conditional to support trove without volume
    # support for now until API supports checking for volume support
    if volume > 0:
        volume_params = {'size': volume}
    else:
        volume_params = None
    return troveclient(request).instances.create(
        name,
        flavor,
        volume=volume_params,
        databases=databases,
        users=users,
        restorePoint=restore_point,
        nics=nics,
        datastore=datastore,
        datastore_version=datastore_version,
        replica_of=replica_of)


def instance_resize_volume(request, instance_id, size):
    return troveclient(request).instances.resize_volume(instance_id, size)


def instance_resize(request, instance_id, flavor_id):
    return troveclient(request).instances.resize_instance(instance_id,
                                                          flavor_id)


def instance_backups(request, instance_id):
    return troveclient(request).instances.backups(instance_id)


def instance_restart(request, instance_id):
    return troveclient(request).instances.restart(instance_id)


def instance_detach_replica(request, instance_id):
    return troveclient(request).instances.edit(instance_id,
                                               detach_replica_source=True)


def database_list(request, instance_id):
    return troveclient(request).databases.list(instance_id)


def database_delete(request, instance_id, db_name):
    return troveclient(request).databases.delete(instance_id, db_name)


def backup_list(request):
    return troveclient(request).backups.list()


def backup_get(request, backup_id):
    return troveclient(request).backups.get(backup_id)


def backup_delete(request, backup_id):
    return troveclient(request).backups.delete(backup_id)


def backup_create(request, name, instance_id, description=None,
                  parent_id=None):
    return troveclient(request).backups.create(name, instance_id,
                                               description, parent_id)


def flavor_list(request):
    return troveclient(request).flavors.list()


def datastore_flavors(request, datastore_name=None,
                      datastore_version=None):
    # if datastore info is available then get datastore specific flavors
    if datastore_name and datastore_version:
        try:
            return troveclient(request).flavors.\
                list_datastore_version_associated_flavors(datastore_name,
                                                          datastore_version)
        except Exception:
            LOG.warn("Failed to retrieve datastore specific flavors")
    return flavor_list(request)


def flavor_get(request, flavor_id):
    return troveclient(request).flavors.get(flavor_id)


def users_list(request, instance_id):
    return troveclient(request).users.list(instance_id)


def user_delete(request, instance_id, user):
    return troveclient(request).users.delete(instance_id, user)


def user_list_access(request, instance_id, user):
    return troveclient(request).users.list_access(instance_id, user)


def datastore_list(request):
    return troveclient(request).datastores.list()


def datastore_version_list(request, datastore):
    return troveclient(request).datastore_versions.list(datastore)
