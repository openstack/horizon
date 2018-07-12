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

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard.api import cinder


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = ("project/snapshots/_detail_overview.html")

    def get_context_data(self, request):
        try:
            snapshot = self.tab_group.kwargs['snapshot']
            volume = cinder.volume_get(request, snapshot.volume_id)
        except Exception:
            redirect = self.get_redirect_url()
            exceptions.handle(self.request,
                              _('Unable to retrieve snapshot details.'),
                              redirect=redirect)
        return {"snapshot": snapshot,
                "volume": volume,
                "group_snapshot": snapshot.group_snapshot}

    def get_redirect_url(self):
        return reverse('horizon:project:snapshots:index')


class SnapshotDetailTabs(tabs.TabGroup):
    slug = "snapshot_details"
    tabs = (OverviewTab,)
