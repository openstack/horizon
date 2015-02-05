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
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm import workflows as idm_workflows


LOG = logging.getLogger('idm_logger')
INDEX_URL = 'horizon:idm:organizations:index'

# ORGANIZATION ROLES
class UserRoleApi(idm_workflows.RelationshipApiInterface):
    """Holds the api calls for each specific relationship"""
    
    def _list_all_owners(self, request, superset_id):
        all_users = api.keystone.user_list(request)
        return [(user.id, user.name) for user in all_users]

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
            msg = (_('Could not find default role "%s" in Keystone') %
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

class UpdateProjectMembersAction(idm_workflows.UpdateRelationshipAction):
    ERROR_MESSAGE = _('Unable to retrieve user list. Please try again later.')
    RELATIONSHIP_CLASS = UserRoleApi
    ERROR_URL = INDEX_URL
    class Meta:
        name = _("Organization Members")
        slug = idm_workflows.RELATIONSHIP_SLUG


class UpdateProjectMembers(idm_workflows.UpdateRelationship):
    action_class = UpdateProjectMembersAction
    available_list_title = _("All Users")
    members_list_title = _("Organization Members")
    no_available_text = _("No users found.")
    no_members_text = _("No users.")
    RELATIONSHIP_CLASS = UserRoleApi


class ManageOrganizationMembers(idm_workflows.RelationshipWorkflow):
    slug = "manage_organization_users"
    name = _("Manage Members")
    finalize_button_name = _("Save")
    success_message = _('Modified users.')
    failure_message = _('Unable to modify users.')
    success_url = "horizon:idm:organizations:detail"
    default_steps = (UpdateProjectMembers,)
    RELATIONSHIP_CLASS = UserRoleApi

    def get_success_url(self):
        # Overwrite to allow passing kwargs
        return reverse(self.success_url, 
                    kwargs={'organization_id':self.context['superset_id']})


# APPLICATION ROLES
class ApplicationRoleApi(idm_workflows.RelationshipApiInterface):
    """FIWARE Roles logic to assign"""
    
    def _list_all_owners(self, request, superset_id):
        all_users = api.keystone.user_list(request)
        project_users_roles = api.keystone.get_project_users_roles(request,
                                             project=superset_id)
        self.available_users = [user for user in all_users
                                     if user.id in project_users_roles]

        #return [(user.id, user.name) for user in all_users]
        return  [(user.id, user.name) for user in self.available_users]

    def _list_all_objects(self, request, superset_id):
        import pdb; pdb.set_trace()
        self.allowed_roles = fiware_api.keystone.list_allowed_roles_to_assign(
                                                request,
                                                user=request.user.id,
                                                organization=superset_id)
        
        # self.allowed_roles = api.keystone.role_list(request)
        return self.allowed_roles

    def _list_current_assignments(self, request, superset_id):
        # NOTE(garcianavalon) logic for this part:
        # load all the organization-scoped application roles for every user
        # but only the ones the user can assign (and only scoped for the current
        # organization)
        import pdb; pdb.set_trace()
        application_users_roles = {}
        for user_id in [user.id for user in self.available_users]:
            application_users_roles[user_id] = [
                r.id for r in fiware_api.keystone.role_list(
                                                    request,
                                                    user=user_id,
                                                    organization=superset_id)
                    if r in self.allowed_roles
            ]
        import pdb; pdb.set_trace()
        return application_users_roles

    def _get_default_object(self, request):
        default_role = api.keystone.get_default_role(request)
        # Default role is necessary to add members to a project
        if default_role is None:
            default = getattr(settings,
                              "OPENSTACK_KEYSTONE_DEFAULT_ROLE", None)
            msg = (_('Could not find default role "%s" in Keystone') %
                   default)
            raise exceptions.NotFound(msg)
        return default_role

    def _add_object_to_owner(self, request, superset, owner, obj):
        fiware_api.keystone.add_role_to_user(request,
                            organization=superset,
                            user=owner,
                            role=obj)

    def _remove_object_from_owner(self, request, superset, owner, obj):
        fiware_api.keystone.remove_role_from_user(request,
                            organization=superset,
                            user=owner,
                            role=obj)

class UpdateApplicationRolesMembersAction(idm_workflows.UpdateRelationshipAction):
    ERROR_MESSAGE = _('Unable to retrieve data. Please try again later.')
    RELATIONSHIP_CLASS = ApplicationRoleApi
    ERROR_URL = INDEX_URL

    class Meta:
        name = _("Manage your applications' roles")
        slug = idm_workflows.RELATIONSHIP_SLUG


class UpdateApplicationRolesMembers(idm_workflows.UpdateRelationship):
    action_class = UpdateApplicationRolesMembersAction
    available_list_title = _("Organization Members")
    members_list_title = _("Members with roles")
    no_available_text = _("No users found.")
    no_members_text = _("No users.")
    RELATIONSHIP_CLASS = ApplicationRoleApi


class ManageApplicationRolesMembers(idm_workflows.RelationshipWorkflow):
    slug = "manage_organization_users_application_roles"
    name = _("Manage your applications' Roles")
    finalize_button_name = _("Save")
    success_message = _('Modified users.')
    failure_message = _('Unable to modify users.')
    success_url = "horizon:idm:organizations:detail"
    default_steps = (UpdateApplicationRolesMembers,)
    RELATIONSHIP_CLASS = ApplicationRoleApi

    def get_success_url(self):
        # Overwrite to allow passing kwargs
        return reverse(self.success_url, 
                    kwargs={'organization_id':self.context['superset_id']})