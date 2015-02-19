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


class ManageAuthorizedMembersLink(tables.LinkAction):
    name = "manage_administrators"
    verbose_name = _("Manage administrators")
    url = "horizon:idm_admin:administrators:members"
    classes = ("ajax-modal",)

    def allowed(self, request, user):
        # TODO(garcianavalon)
        return True


class MembersTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Members'))
    show_avatar = True

    class Meta:
        name = "members"
        verbose_name = _("Authorized Administrators")
        table_actions = (ManageAuthorizedMembersLink, )
        multi_select = False
