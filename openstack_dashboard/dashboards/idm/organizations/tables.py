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

from django.core.exceptions import ValidationError  # noqa
from django.core.urlresolvers import reverse
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from keystoneclient.exceptions import Conflict  # noqa

from openstack_dashboard import api
from openstack_dashboard import policy


class TenantsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'),
                         form_field=forms.CharField(max_length=64))
                         # update_action=UpdateCell)
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'),
                                form_field=forms.CharField(
                                    widget=forms.Textarea(),
                                    required=False))
                                # update_action=UpdateCell)
    clickable = True
    switch = True
    show_avatar = True
    class Meta:
        name = "tenants"
        verbose_name = _("Organizations")
        # row_class = UpdateRow
        # table_actions = (TenantFilterAction, CreateOrganization)
        pagination_param = "tenant_marker"
        multi_select = False

class MyTenantsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'),
                         form_field=forms.CharField(max_length=64))
                         # update_action=UpdateCell)
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'),
                                form_field=forms.CharField(
                                    widget=forms.Textarea(),
                                    required=False))
                                # update_action=UpdateCell)
    clickable = True
    switch = True
    show_avatar = True
    class Meta:
        name = "mytenants"
        verbose_name = _("My Organizations")
        # row_class = UpdateRow
        # table_actions = (TenantFilterAction, CreateOrganization)
        pagination_param = "my_tenant_marker"
        columns = ('name', 'description')
        footer = False
        multi_select = False
       
class MembersTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Member'))
    clickable = True
    show_avatar = True
    class Meta:
        name = "members"
        verbose_name = _("Members")
        footer = False
        multi_select = False

class ApplicationsTable(tables.DataTable):
    name = tables.Column('application', verbose_name=_('Applications'))
    clickable = True
    show_avatar = True
    class Meta:
        name = "applications"
        verbose_name = _("Applications")
        footer = False
        multi_select = False

