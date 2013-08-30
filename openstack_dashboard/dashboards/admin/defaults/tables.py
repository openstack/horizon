# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import logging

from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import tables


LOG = logging.getLogger(__name__)


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
    classes = ("ajax-modal", "btn-edit")


def get_quota_name(quota):
    QUOTA_NAMES = {'cores': _('VCPUs'), 'floating_ips': _('Floating IPs')}
    return QUOTA_NAMES.get(quota.name, quota.name.replace("_", " ").title())


class QuotasTable(tables.DataTable):
    name = tables.Column(get_quota_name, verbose_name=_('Quota Name'))
    limit = tables.Column("limit", verbose_name=_('Limit'))

    def get_object_id(self, obj):
        return obj.name

    class Meta:
        name = "quotas"
        verbose_name = _("Quotas")
        table_actions = (QuotaFilterAction, UpdateDefaultQuotas)
        multi_select = False
