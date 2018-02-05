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

from openstack_dashboard.dashboards.project.volumes import tabs as project_tabs


class OverviewTab(project_tabs.OverviewTab):

    def get_context_data(self, request):
        return {
            'volume': self.tab_group.kwargs['volume'],
            'detail_url': {
                'instance': 'horizon:admin:instances:detail',
                'image': 'horizon:admin:images:detail',
                'encryption': 'horizon:admin:volumes:encryption_detail',
            }
        }


class SnapshotTab(project_tabs.SnapshotTab):
    pass


class VolumeDetailTabs(project_tabs.VolumeDetailTabs):
    tabs = (OverviewTab, project_tabs.SnapshotTab)
