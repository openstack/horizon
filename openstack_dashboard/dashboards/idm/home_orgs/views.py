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

from django.shortcuts import redirect

from horizon import exceptions
from horizon import tables
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm.home_orgs \
    import tables as home_orgs_tables
from openstack_dashboard.dashboards.idm.home_orgs \
    import workflows as home_orgs_workflows


LOG = logging.getLogger('idm_logger')

class IndexView(tables.MultiTableView):
    table_classes = (home_orgs_tables.MembersTable,
                     home_orgs_tables.ApplicationsTable)
    template_name = 'idm/home_orgs/index.html'

    def dispatch(self, request, *args, **kwargs):
        if request.organization.id == request.user.default_project_id:
            return redirect("/idm/")
        return super(IndexView, self).dispatch(request, *args, **kwargs)

    def get_members_data(self):        
        users = []
        try:
            # NOTE(garcianavalon) Filtering by project doesn't work anymore
            # in v3 API >< We need to get the role_assignments for the user's
            # id's and then filter the user list ourselves
            all_users = api.keystone.user_list(self.request)
            project_users_roles = api.keystone.get_project_users_roles(
                self.request,
                project=self.request.organization.id)
            users = [user for user in all_users if user.id in project_users_roles]
        except Exception:
            exceptions.handle(self.request,
                              ("Unable to retrieve member information."))
        return users

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
                              ("Unable to retrieve application list."))
        return idm_utils.filter_default(applications)

class OrganizationMembersView(workflows.WorkflowView):
    workflow_class = home_orgs_workflows.ManageOrganizationMembers

    def get_initial(self):
        initial = super(OrganizationMembersView, self).get_initial()
        initial['superset_id'] = self.request.organization.id
        return initial