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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard.usage import quotas

from openstack_dashboard.dashboards.admin.defaults import tables


class DefaultQuotasTab(tabs.TableTab):
    table_classes = (tables.QuotasTable,)
    name = _("Default Quotas")
    slug = "quotas"
    template_name = ("horizon/common/_detail_table.html")

    def get_quotas_data(self):
        request = self.tab_group.request
        try:
            data = quotas.get_default_quota_data(request)
        except Exception:
            data = []
            exceptions.handle(self.request, _('Unable to get quota info.'))
        return data


class DefaultsTabs(tabs.TabGroup):
    slug = "defaults"
    tabs = (DefaultQuotasTab,)
    sticky = True
