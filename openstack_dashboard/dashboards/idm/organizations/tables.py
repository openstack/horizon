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
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard import api

LOG = logging.getLogger('idm_logger')

class OrganizationsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'))
    avatar = tables.Column(lambda obj: settings.MEDIA_URL + getattr(
        obj, 'img_medium', 'dashboard/img/logos/medium/group.png'))
    default_avatar = tables.Column(lambda obj: settings.STATIC_URL + getattr(
        obj, 'img_medium', 'dashboard/img/logos/medium/group.png'))
    
    clickable = True
    switch = True
    # show_avatar = True

    class Meta:
        name = "organizations"
        verbose_name = _("Organizations")


class MyOrganizationsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'))
    avatar = tables.Column(lambda obj: settings.MEDIA_URL + getattr(
        obj, 'img_medium', 'dashboard/img/logos/medium/group.png'))
    default_avatar = tables.Column(lambda obj: settings.STATIC_URL + getattr(
        obj, 'img_medium', 'dashboard/img/logos/medium/group.png'))
    
    clickable = True
    switch = True
    # show_avatar = True

    class Meta:
        name = "my_organizations"
        verbose_name = _("My Organizations")


class ManageMembersLink(tables.LinkAction):
    name = "manage_members"
    verbose_name = _("Manage Members")
    url = "horizon:idm:organizations:members"
    classes = ("ajax-modal",)

    def allowed(self, request, user):
        # Allowed if he is an admin in the organization
        # TODO(garcianavalon) move to fiware_api
        org_id = self.table.kwargs['organization_id']
        user_roles = api.keystone.roles_for_user(
            request, request.user.id, project=org_id)
        return 'admin' in [r.name for r in user_roles]

    def get_link_url(self, datum=None):
        org_id = self.table.kwargs['organization_id']
        return  urlresolvers.reverse(self.url, args=(org_id,))


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
        verbose_name = _("Members")
        table_actions = (ManageMembersLink, )
        multi_select = False


class AuthorizingApplicationsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Applications'))
    url = tables.Column(lambda obj: getattr(obj, 'url', None))
    avatar = tables.Column(lambda obj: settings.MEDIA_URL + getattr(
        obj, 'img_medium', 'dashboard/img/logos/medium/app.png'))
    default_avatar = tables.Column(lambda obj: settings.STATIC_URL + getattr(
        obj, 'img_medium', 'dashboard/img/logos/medium/app.png'))
    
    clickable = True
    # show_avatar = True

    class Meta:
        name = "applications"
        verbose_name = _("Authorizing Applications")
