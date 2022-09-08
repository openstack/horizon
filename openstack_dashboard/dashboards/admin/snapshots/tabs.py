# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from horizon import tabs

from openstack_dashboard.dashboards.project.snapshots \
    import tables as snap_messages_tables
from openstack_dashboard.dashboards.project.snapshots \
    import tabs as project_tab


class OverviewTab(project_tab.OverviewTab):
    name = _("Overview")
    slug = "overview"
    template_name = ("project/snapshots/_detail_overview.html")

    def get_redirect_url(self):
        return reverse('horizon:admin:snapshots:index')


class SnapshotMessagesTab(project_tab.SnapshotMessagesTab):
    table_classes = (snap_messages_tables.SnapshotMessagesTable,)


class SnapshotDetailsTabs(tabs.DetailTabsGroup):
    slug = "snapshot_details"
    tabs = (OverviewTab, SnapshotMessagesTab)
