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

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm import workflows as idm_workflows


INDEX_URL = "horizon:idm_admin:administrators:index"
LOG = logging.getLogger('idm_logger')


class AuthorizedMembersApi(idm_workflows.RelationshipApiInterface):
    """FIWARE Roles logic to assign"""

    def _list_all_owners(self, request, superset_id):
        all_users = api.keystone.user_list(request)
        return [(user.id, user.name) for user in all_users]

    def _list_all_objects(self, request, superset_id):
        all_roles = fiware_api.keystone.role_list(request)
        default_org = api.keystone.user_get(
            request, request.user).default_project_id
        allowed = fiware_api.keystone.list_user_allowed_roles_to_assign(
            request,
            user=request.user.id,
            organization=default_org)
        self.allowed = [role for role in all_roles 
                   if role.id in allowed[superset_id]]
        return self.allowed

    def _list_current_assignments(self, request, superset_id):
        # NOTE(garcianavalon) logic for this part:
        # load all the organization-scoped application roles for every user
        # but only the ones the user can assign
        application_users_roles = {}
        allowed_ids = [r.id for r in self.allowed]
        role_assignments = fiware_api.keystone.user_role_assignments(
            request, application=superset_id)
        users = set([a.user_id for a in role_assignments])
        for user_id in users:
            application_users_roles[user_id] = [
                a.role_id for a in role_assignments
                if a.user_id == user_id
                and a.role_id in allowed_ids
            ]
        return application_users_roles

    def _get_default_object(self, request):
        return None

    def _add_object_to_owner(self, request, superset, owner, obj):
        default_org = api.keystone.user_get(request, owner).default_project_id
        fiware_api.keystone.add_role_to_user(request,
                                             application=superset,
                                             user=owner,
                                             organization=default_org,
                                             role=obj)

    def _remove_object_from_owner(self, request, superset, owner, obj):
        default_org = api.keystone.user_get(request, owner).default_project_id
        fiware_api.keystone.remove_role_from_user(request,
                                                  application=superset,
                                                  user=owner,
                                                  organization=default_org,
                                                  role=obj)

    def _get_supersetid_name(self, request, superset_id):
        application = fiware_api.keystone.application_get(request, superset_id)
        return application.name


class UpdateAuthorizedMembersAction(idm_workflows.UpdateRelationshipAction):
    ERROR_MESSAGE = ('Unable to retrieve data. Please try again later.')
    RELATIONSHIP_CLASS = AuthorizedMembersApi
    ERROR_URL = INDEX_URL

    class Meta:
        name = ("Manage administrators")
        slug = idm_workflows.RELATIONSHIP_SLUG


class UpdateAuthorizedMembers(idm_workflows.UpdateRelationshipStep):
    action_class = UpdateAuthorizedMembersAction
    available_list_title = ("All users")
    members_list_title = ("Administrators")
    no_available_text = ("No users found.")
    no_members_text = ("No users.")
    RELATIONSHIP_CLASS = AuthorizedMembersApi


class ManageAuthorizedMembers(idm_workflows.RelationshipWorkflow):
    slug = "manage_administrators_roles"
    name = ("Manage Administrators")
    finalize_button_name = ("Save")
    success_message = ('Modified users.')
    failure_message = ('Unable to modify users.')
    success_url = INDEX_URL
    default_steps = (UpdateAuthorizedMembers,)
    RELATIONSHIP_CLASS = AuthorizedMembersApi
