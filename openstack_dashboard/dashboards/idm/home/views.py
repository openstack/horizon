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
            organizations, self._more = api.keystone.tenant_list(self.request,
                                                    user=self.request.user.id,
                                                    admin=False)
            LOG.debug('Organizations listed: {0}'.format(organizations))
        except Exception:
            self._more = False
            exceptions.handle(self.request,
                              _("Unable to retrieve organization list."))
    
        return idm_utils.filter_default_organizations(organizations)

    def get_applications_data(self):
        applications = []
        try:
            applications = fiware_api.keystone.application_list(
                self.request)
                #user=self.request.user.id)
            LOG.debug('Applications listed: {0}'.format(applications))
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve application list."))
        return applications