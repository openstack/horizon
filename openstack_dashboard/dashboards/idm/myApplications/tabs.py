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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm.myApplications \
    import tables as applications_table


class ProvidingTab(tabs.TableTab):
    name = _("Providing")
    slug = "providing_tab"
    table_classes = (applications_table.ProvidingApplicationsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_providing_table_data(self):
        applications = []
        try:
            applications = fiware_api.keystone.application_list(
                self.request)
                #user=self.request.user.id)
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve application list."))
        return applications


class PurchasedTab(tabs.TableTab):
    name = _("Purchased")
    slug = "purchased_tab"
    table_classes = (applications_table.PurchasedApplicationsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_purchased_table_data(self):
        applications = []
        return applications

        
class PanelTabs(tabs.TabGroup):
    slug = "panel_tabs"
    tabs = (ProvidingTab, PurchasedTab)
    sticky = True