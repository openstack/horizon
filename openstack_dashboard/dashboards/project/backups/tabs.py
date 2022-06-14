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

from horizon import exceptions
from horizon import tabs

from openstack_dashboard.api import cinder
from openstack_dashboard.dashboards.project.backups \
    import tables as backup_messages_tables


class BackupOverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = "project/backups/_detail_overview.html"
    redirect_url = 'horizon:project:backups:index'

    def get_context_data(self, request):
        try:
            backup = self.tab_group.kwargs['backup']
            try:
                volume = cinder.volume_get(request, backup.volume_id)
            except Exception:
                volume = None
            try:
                if backup.snapshot_id:
                    snapshot = cinder.volume_snapshot_get(request,
                                                          backup.snapshot_id)
                else:
                    snapshot = None
            except Exception:
                snapshot = None

            return {'backup': backup,
                    'volume': volume,
                    'snapshot': snapshot}

        except Exception:
            redirect = reverse(self.redirect_url)
            exceptions.handle(self.request,
                              _('Unable to retrieve backup details.'),
                              redirect=redirect)


class BackupMessagesTab(tabs.TableTab):
    table_classes = (backup_messages_tables.BackupMessagesTable,)
    name = _("Messages")
    slug = "messages_tab"
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_backup_messages_data(self):
        messages = []
        backup = self.tab_group.kwargs['backup']
        backup_id = backup.id
        try:
            messages = cinder.message_list(self.request, search_opts={
                'resource_type': 'volume_backup', 'resource_uuid': backup_id})
        except Exception:
            exceptions.handle(self.request, _("Unable to retrieve "
                                              "backup messages."))
        return messages


class BackupDetailTabs(tabs.DetailTabsGroup):
    slug = "backup_details"
    tabs = (BackupOverviewTab, BackupMessagesTab)
