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
from horizon import forms

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm import workflows as idm_workflows


LOG = logging.getLogger('idm_logger')
INDEX_URL = 'horizon:idm:members:index'

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
    name = ("Manage your organization members")
    finalize_button_name = ("Save")
    success_message = ('Modified users.')
    failure_message = ('Unable to modify users.')
    success_url = "horizon:idm:members:index"
    default_steps = (UpdateProjectMembers,)
    RELATIONSHIP_CLASS = UserRoleApi
    member_slug = idm_workflows.RELATIONSHIP_SLUG
    current_user_editable = False
    
    def get_success_url(self):
        # Overwrite to allow passing kwargs
        return reverse(self.success_url, 
                    kwargs={'organization_id':self.context['superset_id']})


# APPLICATION MEMBERS
class AuthorizedMembersApi(idm_workflows.RelationshipApiInterface):
    """FIWARE roles and user logic"""
    
    def _list_all_owners(self, request, superset_id):
        # NOTE(garcianavalon) Filtering by project doesn't work anymore
        # in v3 API >< We need to get the role_assignments for the user's
        # id's and then filter the user list ourselves
        all_users = api.keystone.user_list(request)
        project_users_roles = api.keystone.get_project_users_roles(
            request,
            project=superset_id)
        members = [user for user in all_users if user.id in project_users_roles]
        return  [(user.id, user.username) for user in members]


    def _list_all_objects(self, request, superset_id):
        # TODO(garcianavalon) move to fiware_api
        all_roles = fiware_api.keystone.role_list(request)
        allowed = fiware_api.keystone.list_organization_allowed_roles_to_assign(
            request,
            organization=superset_id)
        self.allowed = {}
        for application in allowed:
            self.allowed[application] = [role for role in all_roles 
                                         if role.id in allowed[application]]
        return self.allowed

    def _list_current_assignments(self, request, superset_id):
        # NOTE(garcianavalon) logic for this part:
        # load all the organization-scoped application roles for every user
        # but only the ones the user can assign
        application_users_roles = {}
        for application in self.allowed:
            application_users_roles[application] = {}
            allowed_ids = [r.id for r in self.allowed[application]]
            role_assignments = fiware_api.keystone.user_role_assignments(
                    request, application=application, organization=superset_id)
            users = set([a.user_id for a in role_assignments])
            for user_id in users:
                application_users_roles[application][user_id] = [
                    a.role_id for a in role_assignments
                    if a.user_id == user_id
                    and a.role_id in allowed_ids
                ]
        return application_users_roles


    def _get_default_object(self, request):
        return None


    def _add_object_to_owner(self, request, superset, 
                             owner, obj, application):
        fiware_api.keystone.add_role_to_user(request,
                                             application=application,
                                             user=owner,
                                             organization=superset,
                                             role=obj)

    def _remove_object_from_owner(self, request, superset, 
                                  owner, obj, application):
        fiware_api.keystone.remove_role_from_user(request,
                                                  application=application,
                                                  user=owner,
                                                  organization=superset,
                                                  role=obj)

    def _get_supersetid_name(self, request, superset_id):
        application = fiware_api.keystone.application_get(request, superset_id)
        return application.name


class UpdateAuthorizedMembersAction(idm_workflows.UpdateRelationshipAction):
    ERROR_MESSAGE = ('Unable to retrieve user list. Please try again later.')
    RELATIONSHIP_CLASS = AuthorizedMembersApi
    ERROR_URL = INDEX_URL

    def _init_object_fields(self, object_list, owners_list):
        relationship = self._load_relationship_api()
        for superset_id in object_list:
            for obj in object_list[superset_id]:
                field_name = self.get_member_field_name(
                    superset_id + '-' + obj.id)
                label = obj.name
                widget = forms.widgets.SelectMultiple(attrs={
                    'data-superset-name': 
                        relationship._get_supersetid_name(self.request, 
                                                          superset_id),
                    'data-superset-id':superset_id
                })
                self.fields[field_name] = forms.MultipleChoiceField(
                                                        required=False,
                                                        label=label,
                                                        widget=widget)
                self.fields[field_name].choices = owners_list
                self.fields[field_name].initial = []

    def _init_current_assignments(self, owners_objects_relationship):
        for superset_id in owners_objects_relationship:
            for owner_id in owners_objects_relationship[superset_id]:
                objects_ids = owners_objects_relationship[superset_id][owner_id]
                for object_id in objects_ids:
                    field_name = self.get_member_field_name(
                        superset_id + '-' + object_id)
                    self.fields[field_name].initial.append(owner_id)

    class Meta:
        name = ("Organization Members")
        slug = idm_workflows.RELATIONSHIP_SLUG


class UpdateAuthorizedMembers(idm_workflows.UpdateRelationshipStep):
    action_class = UpdateAuthorizedMembersAction
    available_list_title = ("Organization Members")
    members_list_title = ("Authorized in applications")
    no_available_text = ("No users found.")
    no_members_text = ("No users.")
    RELATIONSHIP_CLASS = AuthorizedMembersApi

    def contribute(self, data, context):
        superset_id = context['superset_id']
        if data:
            self.relationship = self._load_relationship_api()
            try:
                object_list = self.relationship._list_all_objects(
                    self.workflow.request, superset_id)
            except Exception:
                exceptions.handle(self.workflow.request,
                                  ('Unable to retrieve list.'))

            post = self.workflow.request.POST
            for application in object_list:
                for obj in object_list[application]:
                    field = self.get_member_field_name(
                        application + '-' + obj.id)
                    context[field] = post.getlist(field)
        return context


class ManageOrganizationAuthorizedMembers(idm_workflows.RelationshipWorkflow):
    slug = "manage_organization_authorized_users"
    name = ("Authorize Members")
    finalize_button_name = ("Save")
    success_message = ('Modified users.')
    failure_message = ('Unable to modify users.')
    success_url = "horizon:idm:members:index"
    default_steps = (UpdateAuthorizedMembers,)
    RELATIONSHIP_CLASS = AuthorizedMembersApi
    member_slug = idm_workflows.RELATIONSHIP_SLUG

    def handle(self, request, data):
        superset_id = data['superset_id']
        member_step = self.get_step(self.member_slug)
        self.relationship = self._load_relationship_api()
        try:
            object_list = self.relationship._list_all_objects(
                request, superset_id)
            owners_objects_relationship = \
                self.relationship._list_current_assignments(request,
                                                            superset_id)
            # Parse the form data
            modified_objects = {}
            for application in object_list:
                for obj in object_list[application]:
                    field_name = member_step.get_member_field_name(
                        application + '-' + obj.id)
                    modified_objects[obj.id] = data[field_name]
            
                # re-index by object with a owner list for easier processing 
                # in later steps
                current_objects = idm_utils.swap_dict(
                    owners_objects_relationship[application])

                # Create the delete and add sets
                objects_to_add, objects_to_delete = \
                    self._create_add_and_delete_sets(modified_objects, 
                                                     current_objects)
                # Add the objects
                for object_id in objects_to_add:
                    for owner_id in objects_to_add[object_id]:
                      self.relationship._add_object_to_owner(
                        self.request,
                        superset=superset_id,
                        owner=owner_id,
                        obj=object_id,
                        application=application)
                # Remove the objects
                for object_id in objects_to_delete:
                    for owner_id in objects_to_delete[object_id]:
                       self.relationship._remove_object_from_owner(
                            self.request,
                            superset=superset_id,
                            owner=owner_id,
                            obj=object_id,
                            application=application)
            return True
        except Exception:
            exceptions.handle(request,
                          ('Failed to modify organization\'s members.'))
            return False
