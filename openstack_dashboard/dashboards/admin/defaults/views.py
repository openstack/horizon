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

from horizon import tabs
from horizon import workflows

from openstack_dashboard.dashboards.admin.defaults import tabs as project_tabs
from openstack_dashboard.dashboards.admin.defaults import workflows as \
    project_workflows
from openstack_dashboard.usage import quotas


class IndexView(tabs.TabbedTableView):
    tab_group_class = project_tabs.DefaultsTabs
    template_name = 'admin/defaults/index.html'
    page_title = _("Defaults")


class UpdateDefaultQuotasView(workflows.WorkflowView):
    workflow_class = project_workflows.UpdateDefaultQuotas

    def get_initial(self):
        initial = super(UpdateDefaultQuotasView, self).get_initial()

        # get initial quota defaults
        try:
            quota_defaults = quotas.get_default_quota_data(self.request)
            for field in quotas.QUOTA_FIELDS:
                initial[field] = quota_defaults.get(field).limit

        except Exception:
            error_msg = _('Unable to retrieve default quota values.')
            self.add_error_to_step(error_msg, 'update_default_quotas')

        return initial
