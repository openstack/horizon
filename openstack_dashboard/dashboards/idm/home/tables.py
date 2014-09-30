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
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from horizon import exceptions
from horizon import forms
from horizon import tables
from keystoneclient.exceptions import Conflict  # noqa

from openstack_dashboard import api
from openstack_dashboard import policy

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
    url = "horizon:idm:applications"
    
    def get_link_url(self):
        base_url = '/idm/applications/'
        return base_url
        



class TenantsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'),
                         form_field=forms.CharField(max_length=64))
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'),
                                form_field=forms.CharField(
                                    widget=forms.Textarea(),
                                    required=False))
    id = tables.Column('id', verbose_name=_('Project ID'))
    enabled = tables.Column('enabled', verbose_name=_('Enabled'), status=True,
                            form_field=forms.BooleanField(
                                label=_('Enabled'),
                                required=False))
    

    class Meta:
        name = "tenants"
        verbose_name = _("Organizations")
        pagination_param = "tenant_marker"
        table_actions = (GoToOrganizationTable,)
        

class ApplicationsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'),
                         form_field=forms.CharField(max_length=64))
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'),
                                form_field=forms.CharField(
                                    widget=forms.Textarea(),
                                    required=False))
    # id = tables.Column('id', verbose_name=_('Project ID'))
    # enabled = tables.Column('enabled', verbose_name=_('Enabled'), status=True,
    #                         form_field=forms.BooleanField(
    #                             label=_('Enabled'),
    #                             required=False))
    

    class Meta:
        name = "applications"
        verbose_name = _("My Applications")
        pagination_param = "tenant_marker"
        table_actions = (GoToApplicationsTable,)
        
        
