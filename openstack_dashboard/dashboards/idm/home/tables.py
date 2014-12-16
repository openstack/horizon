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


class GoToOrganizationTable(tables.LinkAction):
    name = "organizations"
    verbose_name = _("View All")
    url = "horizon:idm:organizations"

    def get_link_url(self):
        base_url = '/idm/organizations/'
        return base_url


class GoToApplicationsTable(tables.LinkAction):
    name = "applications"
    verbose_name = _("View All")
    url = "horizon:idm:myApplications"

    def get_link_url(self):
        base_url = '/idm/myApplications/'
        return base_url


class CreateOrganization(tables.LinkAction):
    name = "create_organization"
    verbose_name = _("Create")
    url = "horizon:idm:organizations:create"

    def get_link_url(self):
        base_url = '/idm/organizations/create'
        return base_url


class OrganizationsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))
   
    clickable = True
    switch = True
    show_avatar = True
    class Meta:
        name = "organizations"
        verbose_name = _("Organizations")
        table_actions = (CreateOrganization, GoToOrganizationTable,)
        multi_select = False

class ApplicationsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))
    url = tables.Column(lambda obj: getattr(obj, 'url', None))
    
    clickable = True
    show_avatar = True
    class Meta:
        name = "applications"
        verbose_name = _("Applications")
        table_actions = (GoToApplicationsTable,)
        multi_select = False
        
