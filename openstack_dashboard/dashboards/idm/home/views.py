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

import logging

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm.home import tables as home_tables


LOG = logging.getLogger('idm_logger')

class IndexView(tables.MultiTableView):
    table_classes = (home_tables.OrganizationsTable,
                     home_tables.ApplicationsTable)
    template_name = 'idm/home/index.html'

    def has_more_data(self, table):
        return self._more

    def get_organizations_data(self):
        organizations = []
        # domain_context = self.request.session.get('domain_context', None)
        try:
            organizations, self._more = api.keystone.tenant_list(
                self.request,
                user=self.request.user.id,
                admin=False)
            LOG.debug('Organizations listed: {0}'.format(organizations))
        except Exception:
            self._more = False
            exceptions.handle(self.request,
                              _("Unable to retrieve organization list."))
    
        return idm_utils.filter_default(organizations)

    def get_applications_data(self):
        applications = []
        try:
            # TODO(garcianavalon) extract to fiware_api
            all_apps = fiware_api.keystone.application_list(self.request)
            apps_with_roles = [a.application_id for a 
                               in fiware_api.keystone.user_role_assignments(
                               self.request, user=self.request.user.id)]
            applications = [app for app in all_apps 
                            if app.id in apps_with_roles]
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve application list."))
        return idm_utils.filter_default(applications)