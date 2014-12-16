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

from django.utils.translation import ugettext_lazy as _

from horizon import tables


class OrganizationsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'))
    clickable = True
    switch = True
    show_avatar = True

    class Meta:
        name = "organizations"
        verbose_name = _("Organizations")


class MyOrganizationsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'))
    clickable = True
    switch = True
    show_avatar = True

    class Meta:
        name = "my_organizations"
        verbose_name = _("My Organizations")


class AddMemberLink(tables.LinkAction):
    name = "add"
    verbose_name = _("Add")
    url = "horizon:idm:organizations:index"
    classes = ("ajax-modal",)

    def allowed(self, request, user):
        # TODO(garcianavalon)
        return True

class MembersTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Members'))
    show_avatar = True

    class Meta:
        name = "members"
        verbose_name = _("Authorized members")
        table_actions = (AddMemberLink, )
        multi_select = False


class ApplicationsTable(tables.DataTable):
    name = tables.Column('application', verbose_name=_('Applications'))
    clickable = True
    show_avatar = True

    class Meta:
        name = "applications"
        verbose_name = _("Applications")
