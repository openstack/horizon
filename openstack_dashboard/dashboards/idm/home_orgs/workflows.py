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
from django.core.urlresolvers import reverse

from horizon import exceptions

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm import workflows as idm_workflows


LOG = logging.getLogger('idm_logger')
INDEX_URL = 'horizon:idm:home_orgs:index'

# ORGANIZATION ROLES
class UserRoleApi(idm_workflows.RelationshipApiInterface):
    """Holds the api calls for each specific relationship"""
    
    def _list_all_owners(self, request, superset_id):
        all_users = api.keystone.user_list(request)
        return [(user.id, user.username) for user in all_users]

    def _list_all_objects(self, request, superset_id):
        return api.keystone.role_list(request)

    def _list_current_assignments(self, request, superset_id):
        return api.keystone.get_project_users_roles(request,
                                        project=superset_id)

    def _get_default_object(self, request):
        default_role = api.keystone.get_default_role(request)
        # Default role is necessary to add members to a project
        if default_role is None:
            default = getattr(settings,
                              "OPENSTACK_KEYSTONE_DEFAULT_ROLE", None)
            msg = (('Could not find default role "%s" in Keystone') %
                   default)
            raise exceptions.NotFound(msg)
        return default_role

    def _add_object_to_owner(self, request, superset, owner, obj):
        api.keystone.add_tenant_user_role(request,
                            project=superset,
                            user=owner,
                            role=obj)
                    

    def _remove_object_from_owner(self, request, superset, owner, obj):
        api.keystone.remove_tenant_user_role(request,
                            project=superset,
                            user=owner,
                            role=obj)

    def _get_supersetid_name(self, request, superset_id):
        organization = api.keystone.tenant_get(request, superset_id)
        return organization.name


class UpdateProjectMembersAction(idm_workflows.UpdateRelationshipAction):
    ERROR_MESSAGE = ('Unable to retrieve user list. Please try again later.')
    RELATIONSHIP_CLASS = UserRoleApi
    ERROR_URL = INDEX_URL
    class Meta:
        name = ("Organization Members")
        slug = idm_workflows.RELATIONSHIP_SLUG


class UpdateProjectMembers(idm_workflows.UpdateRelationshipStep):
    action_class = UpdateProjectMembersAction
    available_list_title = ("All Users")
    members_list_title = ("Organization Members")
    no_available_text = ("No users found.")
    no_members_text = ("No users.")
    RELATIONSHIP_CLASS = UserRoleApi


class ManageOrganizationMembers(idm_workflows.RelationshipWorkflow):
    slug = "manage_organization_users"
    name = ("Manage Members")
    finalize_button_name = ("Save")
    success_message = ('Modified users.')
    failure_message = ('Unable to modify users.')
    success_url = "horizon:idm:members:index"
    default_steps = (UpdateProjectMembers,)
    RELATIONSHIP_CLASS = UserRoleApi
    member_slug = idm_workflows.RELATIONSHIP_SLUG
    
    # def get_success_url(self):
    #     # Overwrite to allow passing kwargs
    #     return reverse(self.success_url, 
    #                 kwargs={'organization_id':self.context['superset_id']})


