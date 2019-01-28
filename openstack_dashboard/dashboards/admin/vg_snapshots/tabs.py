# Copyright 2019 NEC Corporation
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

from openstack_dashboard.dashboards.project.vg_snapshots \
    import tabs as project_tabs


class OverviewTab(project_tabs.OverviewTab):
    template_name = "admin/vg_snapshots/_detail_overview.html"

    def get_redirect_url(self):
        return reverse('horizon:admin:vg_snapshots:index')


class DetailTabs(project_tabs.DetailTabs):
    tabs = (OverviewTab,)
