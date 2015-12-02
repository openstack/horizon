# Copyright (c) 2014 eBay Software Foundation
# Copyright 2015 HP Software, LLC
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

from django.core import urlresolvers
from django.template.defaultfilters import title  # noqa
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables
from horizon.templatetags import sizeformat
from horizon.utils import filters
from horizon.utils import memoized
from openstack_dashboard.contrib.trove import api
from openstack_dashboard.contrib.trove.content.databases import db_capability

ACTIVE_STATES = ("ACTIVE",)


class DeleteCluster(tables.BatchAction):
    name = "delete"
    icon = "remove"
    classes = ('btn-danger',)
    help_text = _("Deleted cluster is not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Cluster",
            u"Delete Clusters",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Cluster",
            u"Scheduled deletion of Clusters",
            count
        )

    def action(self, request, obj_id):
        api.trove.cluster_delete(request, obj_id)


class LaunchLink(tables.LinkAction):
    name = "launch"
    verbose_name = _("Launch Cluster")
    url = "horizon:project:database_clusters:launch"
    classes = ("btn-launch", "ajax-modal")
    icon = "cloud-upload"


class AddShard(tables.LinkAction):
    name = "add_shard"
    verbose_name = _("Add Shard")
    url = "horizon:project:database_clusters:add_shard"
    classes = ("ajax-modal",)
    icon = "plus"

    def allowed(self, request, cluster=None):
        if (cluster and cluster.task["name"] == 'NONE' and
                db_capability.is_mongodb_datastore(cluster.datastore['type'])):
            return True
        return False


class ResetPassword(tables.LinkAction):
    name = "reset_password"
    verbose_name = _("Reset Root Password")
    url = "horizon:project:database_clusters:reset_password"
    classes = ("ajax-modal",)

    def allowed(self, request, cluster=None):
        if (cluster and cluster.task["name"] == 'NONE' and
                db_capability.is_vertica_datastore(cluster.datastore['type'])):
            return True
        return False

    def get_link_url(self, datum):
        cluster_id = self.table.get_object_id(datum)
        return urlresolvers.reverse(self.url, args=[cluster_id])


class UpdateRow(tables.Row):
    ajax = True

    @memoized.memoized_method
    def get_data(self, request, cluster_id):
        cluster = api.trove.cluster_get(request, cluster_id)
        try:
            # TODO(michayu): assumption that cluster is homogeneous
            flavor_id = cluster.instances[0]['flavor']['id']
            cluster.full_flavor = api.trove.flavor_get(request, flavor_id)
        except Exception:
            pass
        return cluster


def get_datastore(cluster):
    return cluster.datastore["type"]


def get_datastore_version(cluster):
    return cluster.datastore["version"]


def get_size(cluster):
    if db_capability.is_vertica_datastore(cluster.datastore['type']):
        return "3"

    if hasattr(cluster, "full_flavor"):
        size_string = _("%(name)s | %(RAM)s RAM | %(instances)s instances")
        vals = {'name': cluster.full_flavor.name,
                'RAM': sizeformat.mbformat(cluster.full_flavor.ram),
                'instances': len(cluster.instances)}
        return size_string % vals
    return _("Not available")


def get_task(cluster):
    return cluster.task["name"]


class ClustersTable(tables.DataTable):
    TASK_CHOICES = (
        ("none", True),
    )
    name = tables.Column("name",
                         link=("horizon:project:database_clusters:detail"),
                         verbose_name=_("Cluster Name"))
    datastore = tables.Column(get_datastore,
                              verbose_name=_("Datastore"))
    datastore_version = tables.Column(get_datastore_version,
                                      verbose_name=_("Datastore Version"))
    size = tables.Column(get_size,
                         verbose_name=_("Cluster Size"),
                         attrs={'data-type': 'size'})
    task = tables.Column(get_task,
                         filters=(title, filters.replace_underscores),
                         verbose_name=_("Current Task"),
                         status=True,
                         status_choices=TASK_CHOICES)

    class Meta(object):
        name = "clusters"
        verbose_name = _("Clusters")
        status_columns = ["task"]
        row_class = UpdateRow
        table_actions = (LaunchLink, DeleteCluster)
        row_actions = (AddShard, ResetPassword, DeleteCluster)


def get_instance_size(instance):
    if hasattr(instance, "full_flavor"):
        size_string = _("%(name)s | %(RAM)s RAM")
        vals = {'name': instance.full_flavor.name,
                'RAM': sizeformat.mbformat(instance.full_flavor.ram)}
        return size_string % vals
    return _("Not available")


def get_instance_type(instance):
    if hasattr(instance, "type"):
        return instance.type
    return _("Not available")


def get_host(instance):
    if hasattr(instance, "hostname"):
        return instance.hostname
    elif hasattr(instance, "ip") and instance.ip:
        return instance.ip[0]
    return _("Not Assigned")


class InstancesTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"))
    type = tables.Column(get_instance_type,
                         verbose_name=_("Type"))
    host = tables.Column(get_host,
                         verbose_name=_("Host"))
    size = tables.Column(get_instance_size,
                         verbose_name=_("Size"),
                         attrs={'data-type': 'size'})
    status = tables.Column("status",
                           filters=(title, filters.replace_underscores),
                           verbose_name=_("Status"))

    class Meta(object):
        name = "instances"
        verbose_name = _("Instances")
