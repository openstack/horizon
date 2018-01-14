# Copyright 2013 Kylin, Inc.
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

from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard.usage import quotas


class QuotaFilterAction(tables.FilterAction):
    def filter(self, table, tenants, filter_string):
        q = filter_string.lower()

        def comp(tenant):
            if q in tenant.name.lower():
                return True
            return False

        return filter(comp, tenants)


class UpdateDefaultQuotas(tables.LinkAction):
    name = "update_defaults"
    verbose_name = _("Update Defaults")
    url = "horizon:admin:defaults:update_defaults"
    classes = ("ajax-modal",)
    icon = "pencil"
    step = None

    def get_link_url(self, datum=None):
        url = [reverse(self.url)]
        if self.step:
            url.append(urlencode({'step': self.step}))
        return '?'.join(url)

    def allowed(self, request, _=None):
        return quotas.enabled_quotas(request)


class UpdateDefaultComputeQuotas(UpdateDefaultQuotas):
    name = 'update_compute_defaults'
    step = 'update_default_compute_quotas'


class UpdateDefaultVolumeQuotas(UpdateDefaultQuotas):
    name = 'update_volume_defaults'
    step = 'update_default_volume_quotas'


def get_compute_quota_name(quota):
    QUOTA_NAMES = {
        'injected_file_content_bytes': _('Injected File Content Bytes'),
        'injected_file_path_bytes': _('Length of Injected File Path'),
        'metadata_items': _('Metadata Items'),
        'cores': _('VCPUs'),
        'instances': _('Instances'),
        'injected_files': _('Injected Files'),
        'ram': _('RAM (MB)'),
        'key_pairs': _('Key Pairs'),
        'server_group_members': _('Server Group Members'),
        'server_groups': _('Server Groups'),
    }
    return QUOTA_NAMES.get(quota.name, quota.name.replace("_", " ").title())


class ComputeQuotasTable(tables.DataTable):
    name = tables.Column(get_compute_quota_name, verbose_name=_('Quota Name'))
    limit = tables.Column("limit", verbose_name=_('Limit'))

    def get_object_id(self, obj):
        return obj.name

    class Meta(object):
        name = "compute_quotas"
        verbose_name = _("Compute Quotas")
        table_actions = (QuotaFilterAction, UpdateDefaultComputeQuotas)
        multi_select = False


def get_volume_quota_name(quota):
    QUOTA_NAMES = {
        'volumes': _('Volumes'),
        'snapshots': _('Volume Snapshots'),
        'backups': _('Backups'),
        'gigabytes': _('Total Size of Volumes and Snapshots (GiB)'),
        'backup_gigabytes': _('Backup Size (GiB)'),
        'per_volume_gigabytes': _('Per Volume Size (GiB)'),
        'groups': _('Volume Groups'),
        'dm-crypt': _('dm-crypt'),
    }

    QUOTA_DYNAMIC_NAMES = {
        'volumes': _('Volumes of Type %(type)s'),
        'snapshots': _('Volume Snapshots of Type %(type)s'),
        'gigabytes':
            _('Total Size of Volumes and Snapshots (GiB) of Type %(type)s')
    }

    # NOTE(Itxaka): This quotas are dynamic and depend on the type of
    # volume types that are defined by the operator
    if quota.name.startswith(('volumes_', 'snapshots_', 'gigabytes_')):
        params = {'type': quota.name.split('_')[1]}
        return QUOTA_DYNAMIC_NAMES.get(quota.name.split('_')[0]) % params
    return QUOTA_NAMES.get(quota.name, quota.name.replace("_", " ").title())


class VolumeQuotasTable(tables.DataTable):
    name = tables.Column(get_volume_quota_name, verbose_name=_('Quota Name'))
    limit = tables.Column("limit", verbose_name=_('Limit'))

    def get_object_id(self, obj):
        return obj.name

    class Meta(object):
        name = "volume_quotas"
        verbose_name = _("Volume Quotas")
        table_actions = (QuotaFilterAction, UpdateDefaultVolumeQuotas)
        multi_select = False


def get_network_quota_name(quota):
    QUOTA_NAMES = {
        'network': _('Networks'),
        'subnet': _('Subnets'),
        'port': _('Ports'),
        'subnetpool': _('Subnet Pool'),
        'router': _('Routers'),
        'floatingip': _('Floating IPs'),
        'security_group': _('Security Groups'),
        'security_group_rule': _('Security Group Rules'),
        'rbac_policy': _('RBAC Policies'),
        'trunk': _('Trunks'),
    }
    return QUOTA_NAMES.get(quota.name, quota.name.replace("_", " ").title())


class NetworkQuotasTable(tables.DataTable):
    name = tables.Column(get_network_quota_name, verbose_name=_('Quota Name'))
    limit = tables.Column("limit", verbose_name=_('Limit'))

    def get_object_id(self, obj):
        return obj.name

    class Meta(object):
        name = "network_quotas"
        verbose_name = _("Network Quotas")
        table_actions = (QuotaFilterAction,)
        multi_select = False
