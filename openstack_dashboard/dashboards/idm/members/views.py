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

from django.shortcuts import redirect

from horizon import exceptions
from horizon import tables
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm.members \
    import tables as members_tables
from openstack_dashboard.dashboards.idm.members \
    import workflows as members_workflows


LOG = logging.getLogger('idm_logger')

class IndexView(tables.MultiTableView):
    table_classes = (members_tables.MembersTable,)
    template_name = 'idm/members/index.html'

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


class OrganizationMembersView(workflows.WorkflowView):
    workflow_class = members_workflows.ManageOrganizationMembers

    def get_initial(self):
        initial = super(OrganizationMembersView, self).get_initial()
        initial['superset_id'] = self.request.organization.id
        return initial