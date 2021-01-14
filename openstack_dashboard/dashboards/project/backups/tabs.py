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
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard.api import cinder


class BackupOverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = "project/backups/_detail_overview.html"

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
            redirect = reverse('horizon:project:backups:index')
            exceptions.handle(self.request,
                              _('Unable to retrieve backup details.'),
                              redirect=redirect)


class BackupDetailTabs(tabs.TabGroup):
    slug = "backup_details"
    tabs = (BackupOverviewTab,)
