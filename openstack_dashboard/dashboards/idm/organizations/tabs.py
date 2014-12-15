# Copyright (C) 2014 Universidad Politecnica de Madrid
#
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

from openstack_dashboard import api
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm.organizations \
    import tables as organization_tables


class OrganizationsTab(tabs.TableTab):
    name = _("Other")
    slug = "organizations_tab"
    table_classes = (organization_tables.OrganizationsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def has_more_data(self, table):
        return self._more

    def get_organizations_data(self):
        organizations = []
        my_organizations = []
        #domain_context = self.request.session.get('domain_context', None)
        try:
            organizations, self._more = api.keystone.tenant_list(self.request,
                                                            admin=False)
            my_organizations, self._more = api.keystone.tenant_list(self.request,
                                            user=self.request.user.id,
                                            admin=False)
            organizations = [t for t in organizations if not t in my_organizations]
        except Exception as e:
            self._more = False
            exceptions.handle(self.request,
                              _("Unable to retrieve organization list. \
                                    Error message: {0}".format(e)))
        return idm_utils.filter_default_organizations(organizations)


class MyOrganizationsTab(tabs.TableTab):
    name = _("Owned")
    slug = "my_organizations_tab"
    table_classes = (organization_tables.MyOrganizationsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def has_more_data(self, table):
        return self._more

    def get_my_organizations_data(self):
        organizations = []
        #domain_context = self.request.session.get('domain_context', None)
        try:
            organizations, self._more = api.keystone.tenant_list(
                self.request,
                user=self.request.user.id,
                admin=False)
        except Exception:
            self._more = False
            exceptions.handle(self.request,
                              _("Unable to retrieve organization information."))
        return idm_utils.filter_default_organizations(organizations)


class PanelTabs(tabs.TabGroup):
    slug = "panel_tabs"
    tabs = (MyOrganizationsTab, OrganizationsTab)
    sticky = True