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

import logging

from django.conf import settings

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm.myApplications \
    import tables as applications_table


LOG = logging.getLogger('idm_logger')

class ProvidingTab(tabs.TableTab):
    name = ("Providing")
    slug = "providing_tab"
    table_classes = (applications_table.ProvidingApplicationsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_providing_table_data(self):
        applications = []
        try:
            # TODO(garcianavalon) extract to fiware_api
            provider_role = fiware_api.keystone.get_provider_role(self.request)
            all_apps = fiware_api.keystone.application_list(self.request)
            apps_with_roles = [a.application_id for a 
                               in fiware_api.keystone.user_role_assignments(
                               self.request, user=self.request.user.id)
                               if a.role_id == provider_role.id]
            applications = [app for app in all_apps 
                            if app.id in apps_with_roles]
            
        except Exception:
            exceptions.handle(self.request,
                              ("Unable to retrieve application list."))
        return idm_utils.filter_default(applications)


class PurchasedTab(tabs.TableTab):
    name = ("Purchased")
    slug = "purchased_tab"
    table_classes = (applications_table.PurchasedApplicationsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_purchased_table_data(self):
        applications = []
        try:
            # TODO(garcianavalon) extract to fiware_api
            purchaser_role = fiware_api.keystone.get_purchaser_role(self.request)
            all_apps = fiware_api.keystone.application_list(self.request)
            apps_with_roles = [a.application_id for a 
                               in fiware_api.keystone.user_role_assignments(
                               self.request, user=self.request.user.id)
                               if a.role_id == purchaser_role.id]
            applications = [app for app in all_apps 
                            if app.id in apps_with_roles]
            
        except Exception:
            exceptions.handle(self.request,
                              ("Unable to retrieve application list."))
        return idm_utils.filter_default(applications)


class AuthorizedTab(tabs.TableTab):
    name = ("Authorized")
    slug = "authorized_tab"
    table_classes = (applications_table.AuthorizedApplicationsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_authorized_table_data(self):
        applications = []
        try:
            # TODO(garcianavalon) extract to fiware_api
            purchaser_role = fiware_api.keystone.get_purchaser_role(self.request)
            provider_role = fiware_api.keystone.get_provider_role(self.request)
            all_apps = fiware_api.keystone.application_list(self.request)
            apps_with_roles = [a.application_id for a 
                               in fiware_api.keystone.user_role_assignments(
                               self.request, user=self.request.user.id)
                               if a.role_id != purchaser_role.id
                               and a.role_id != provider_role.id]
            applications = [app for app in all_apps 
                            if app.id in apps_with_roles]
            
        except Exception:
            exceptions.handle(self.request,
                              ("Unable to retrieve application list."))
        return idm_utils.filter_default(applications)

        
class PanelTabs(tabs.TabGroup):
    slug = "panel_tabs"
    tabs = (ProvidingTab, PurchasedTab, AuthorizedTab)
    sticky = True