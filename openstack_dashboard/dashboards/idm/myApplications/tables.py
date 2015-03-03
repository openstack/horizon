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

from django.core import urlresolvers

from horizon import tables

from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm import tables as idm_tables


class ProvidingApplicationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_APP_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Name'))
    url = tables.Column(lambda obj: getattr(obj, 'url', None))
    
    class Meta:
        name = "providing_table"
        verbose_name = ("")
        multi_select = False
        row_class = idm_tables.ApplicationClickableRow
        

class PurchasedApplicationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_APP_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Name'))
    url = tables.Column(lambda obj: getattr(obj, 'url', None))  
    
    class Meta:
        name = "purchased_table"
        verbose_name = ("")
        multi_select = False
        row_class = idm_tables.ApplicationClickableRow


class AuthorizedApplicationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_APP_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Name'))
    url = tables.Column(lambda obj: getattr(obj, 'url', None))  

    class Meta:
        name = "authorized_table"
        verbose_name = ("")
        multi_select = False
        row_class = idm_tables.ApplicationClickableRow


class ManageAuthorizedMembersLink(tables.LinkAction):
    name = "manage_application_members"
    verbose_name = ("Authorize")
    url = "horizon:idm:myApplications:members"
    classes = ("ajax-modal",)
    icon = "check-square-o"

    def allowed(self, request, user):
        # Allowed if your allowed role list is not empty
        # TODO(garcianavalon) move to fiware_api
        default_org = request.user.default_project_id
        if request.user.default_project_id == request.organization.id:
            allowed = fiware_api.keystone.list_user_allowed_roles_to_assign(
                request,
                user=request.user.id,
                organization=request.user.default_project_id)
        else:
            allowed = fiware_api.keystone.list_organization_allowed_roles_to_assign(
                request,
                organization=request.organization.id)
        app_id = self.table.kwargs['application_id']
        return allowed.get(app_id, False)

    def get_link_url(self, datum=None):
        app_id = self.table.kwargs['application_id']
        return  urlresolvers.reverse(self.url, args=(app_id,))


class MembersTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_USER_MEDIUM_AVATAR))
    username = tables.Column('username', verbose_name=('Members'))
    
    class Meta:
        name = "members"
        verbose_name = ("Authorized Members")
        table_actions = (tables.FilterAction, ManageAuthorizedMembersLink, )
        multi_select = False
        row_class = idm_tables.UserClickableRow


class ManageAuthorizedOrganizationsLink(tables.LinkAction):
    name = "manage_application_organizations"
    verbose_name = ("Authorize")
    url = "horizon:idm:myApplications:organizations"
    classes = ("ajax-modal",)
    icon = "check-square-o"

    def allowed(self, request, user):
        # Allowed if your allowed role list is not empty
        # TODO(garcianavalon) move to fiware_api
        default_org = request.user.default_project_id
        if request.user.default_project_id == request.organization.id:
            allowed = fiware_api.keystone.list_user_allowed_roles_to_assign(
                request,
                user=request.user.id,
                organization=request.user.default_project_id)
        else:
            allowed = fiware_api.keystone.list_organization_allowed_roles_to_assign(
                request,
                organization=request.organization.id)
        app_id = self.table.kwargs['application_id']
        return allowed.get(app_id, False)

    def get_link_url(self, datum=None):
        app_id = self.table.kwargs['application_id']
        return  urlresolvers.reverse(self.url, args=(app_id,))


class AuthorizedOrganizationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_ORG_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Applications'))
    url = tables.Column(lambda obj: getattr(obj, 'url', None))
    

    class Meta:
        name = "organizations"
        verbose_name = ("Authorized Organizations")
        table_actions = (tables.FilterAction, 
            ManageAuthorizedOrganizationsLink, )
        row_class = idm_tables.OrganizationClickableRow