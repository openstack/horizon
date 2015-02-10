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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from horizon import version

from openstack_dashboard.dashboards.admin.info import constants
from openstack_dashboard.dashboards.admin.info import tabs as project_tabs


class IndexView(tabs.TabbedTableView):
    tab_group_class = project_tabs.SystemInfoTabs
    template_name = constants.INFO_TEMPLATE_NAME
    page_title = _("System Information")

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        try:
            context["version"] = version.version_info.version_string()
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve version information.'))

        return context
