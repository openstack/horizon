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

from horizon import tables

from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm import tables as idm_tables


class ManageMembersLink(tables.LinkAction):
    name = "manage_members"
    verbose_name = ("Manage")
    url = "horizon:idm:members:edit"
    classes = ("ajax-modal",)
    icon = "cogs"

class ManageAuthorizedMembersLink(tables.LinkAction):
    name = "manage_authorized_members"
    verbose_name = ("Authorize")
    url = "horizon:idm:members:authorize"
    classes = ("ajax-modal",)
    icon = "check-square-o"

    
class MembersTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_USER_MEDIUM_AVATAR))
    username = tables.Column('username', verbose_name=('Members'))
    

    class Meta:
        name = "members"
        verbose_name = ("Members")
        table_actions = (tables.FilterAction, 
            ManageMembersLink, ManageAuthorizedMembersLink)
        multi_select = False
        row_class = idm_tables.UserClickableRow
