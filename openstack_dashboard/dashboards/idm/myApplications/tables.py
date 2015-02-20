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

from django.conf import settings
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard import api
from openstack_dashboard import fiware_api


class ProvidingApplicationsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))
    url = tables.Column(lambda obj: getattr(obj, 'url', None))
    avatar = tables.Column(lambda obj: settings.MEDIA_URL + getattr(
        obj, 'img_medium', 'dashboard/img/logos/medium/app.png'))
    default_avatar = tables.Column(lambda obj: settings.STATIC_URL + getattr(
        obj, 'img_medium', 'dashboard/img/logos/medium/app.png'))
    
    clickable = True
    # show_avatar = True

    class Meta:
        name = "providing_table"
        verbose_name = _("Providing Applications")
        multi_select = False
        

class PurchasedApplicationsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))
    url = tables.Column(lambda obj: getattr(obj, 'url', None))
    avatar = tables.Column(lambda obj: settings.MEDIA_URL + getattr(
        obj, 'img_medium', 'dashboard/img/logos/medium/app.png'))
    default_avatar = tables.Column(lambda obj: settings.STATIC_URL + getattr(
        obj, 'img_medium', 'dashboard/img/logos/medium/app.png'))
    
    clickable = True
    # show_avatar = True

    class Meta:
        name = "purchased_table"
        verbose_name = _("Purchased Applications")
        multi_select = False


class ManageAuthorizedMembersLink(tables.LinkAction):
    name = "manage_application_members"
    verbose_name = _("Manage authorized users")
    url = "horizon:idm:myApplications:members"
    classes = ("ajax-modal",)

    def allowed(self, request, user):
        # Allowed if your allowed role list is not empty
        # TODO(garcianavalon) move to fiware_api
        default_org = request.user.default_project_id
        allowed = fiware_api.keystone.list_user_allowed_roles_to_assign(
            request,
            user=request.user.id,
            organization=default_org)
        app_id = self.table.kwargs['application_id']
        return allowed.get(app_id, False)

    def get_link_url(self, datum=None):
        app_id = self.table.kwargs['application_id']
        return  urlresolvers.reverse(self.url, args=(app_id,))


class MembersTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Members'))
    avatar = tables.Column(lambda obj: settings.MEDIA_URL + getattr(
        obj, 'img_medium', 'dashboard/img/logos/medium/user.png'))
    default_avatar = tables.Column(lambda obj: settings.STATIC_URL + getattr(
        obj, 'img_medium', 'dashboard/img/logos/medium/user.png'))
    
    # show_avatar = True
    clickable = True

    class Meta:
        name = "members"
        verbose_name = _("Authorized Members")
        table_actions = (ManageAuthorizedMembersLink, )
        multi_select = False


class ManageAuthorizedOrganizationsLink(tables.LinkAction):
    name = "manage_application_organizations"
    verbose_name = _("Manage authorized organizations")
    url = "horizon:idm:myApplications:organizations"
    classes = ("ajax-modal",)

    def allowed(self, request, user):
        # Allowed if your allowed role list is not empty
        # TODO(garcianavalon) move to fiware_api
        default_org = request.user.default_project_id
        allowed = fiware_api.keystone.list_user_allowed_roles_to_assign(
            request,
            user=request.user.id,
            organization=default_org)
        app_id = self.table.kwargs['application_id']
        return allowed.get(app_id, False)

    def get_link_url(self, datum=None):
        app_id = self.table.kwargs['application_id']
        return  urlresolvers.reverse(self.url, args=(app_id,))


class AuthorizedOrganizationsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Applications'))
    url = tables.Column(lambda obj: getattr(obj, 'url', None))
    avatar = tables.Column(lambda obj: settings.MEDIA_URL + getattr(
        obj, 'img_medium', 'dashboard/img/logos/medium/app.png'))
    default_avatar = tables.Column(lambda obj: settings.STATIC_URL + getattr(
        obj, 'img_medium', 'dashboard/img/logos/medium/app.png'))
    
    # show_avatar = True
    clickable = True

    class Meta:
        name = "organizations"
        verbose_name = _("Authorized Organizations")
        table_actions = (ManageAuthorizedOrganizationsLink, )
        multi_select = False