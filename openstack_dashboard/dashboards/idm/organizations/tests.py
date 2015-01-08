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

import unittest

from mox import IsA  # noqa

from django import http
from django.core.urlresolvers import reverse

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from openstack_dashboard.dashboards.idm import tests as idm_tests
from openstack_dashboard.dashboards.idm.organizations \
    import forms as organizations_forms


INDEX_URL = reverse('horizon:idm:organizations:index')
CREATE_URL = reverse('horizon:idm:organizations:create')

class BaseOrganizationsTests(idm_tests.BaseTestCase):

    def _get_project_info(self, project):
        project_info = {
            "name": unicode(project.name),
            "description": unicode(project.description),
            "enabled": project.enabled,
            "domain": IsA(api.base.APIDictWrapper),
            "city": '',
            "email": '',
            "img":IsA(str),
            # '/static/dashboard/img/logos/small/group.png',
            "website" : ''
        }
        return project_info


class IndexTests(BaseOrganizationsTests):

    @test.create_stubs({api.keystone: ('tenant_list',)})
    def test_index(self):
        user_organizations = self.list_organizations()

        # Owned organizations mockup
        # Only calls the default/first tab, no need to mock the others tab
        api.keystone.tenant_list(IsA(http.HttpRequest),
                                user=self.user.id,
                                admin=False).AndReturn((user_organizations, False))
        self.mox.ReplayAll()

        response = self.client.get(INDEX_URL)
        self.assertTemplateUsed(response, 'idm/organizations/index.html')
        self.assertItemsEqual(response.context['table'].data, user_organizations)
        self.assertNoMessages() 

    @test.create_stubs({api.keystone: ('tenant_list',)})
    def test_other_organizations_tab(self):
        all_organizations = self.list_organizations()
        user_organizations = all_organizations[len(all_organizations)/2:]
        other_organizations = all_organizations[:len(all_organizations)/2]
        # Other organizations mockup
        api.keystone.tenant_list(IsA(http.HttpRequest),
                                admin=False).AndReturn((all_organizations, False))
        api.keystone.tenant_list(IsA(http.HttpRequest),
                                user=self.user.id,
                                admin=False).AndReturn((user_organizations, False))
        self.mox.ReplayAll()

        response = self.client.get(INDEX_URL + '?tab=panel_tabs__organizations_tab')
        self.assertTemplateUsed(response, 'idm/organizations/index.html')
        self.assertItemsEqual(response.context['table'].data, other_organizations)
        self.assertNoMessages() 


class DetailTests(BaseOrganizationsTests):

    @test.create_stubs({
        api.keystone: (
            'tenant_get',
            'user_list',
        )
    })
    def test_detail(self):
        project = self.get_organization()
        users = self.users.list()

        api.keystone.user_list(IsA(http.HttpRequest), 
                                project=project.id).AndReturn(users)
        api.keystone.tenant_get(IsA(http.HttpRequest), 
                                project.id,
                                admin=True).AndReturn(project)
        self.mox.ReplayAll()

        url = reverse('horizon:idm:organizations:detail', args=[project.id])
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'idm/organizations/detail.html')
        self.assertItemsEqual(response.context['members_table'].data, users)
        self.assertNoMessages() 


class CreateTests(BaseOrganizationsTests):

    @test.create_stubs({api.keystone: ('tenant_create',)})
    def test_create_organization(self):
        project = self.get_organization()
        project_details = self._get_project_info(project)

        api.keystone.tenant_create(IsA(http.HttpRequest), 
                                    **project_details).AndReturn(project)

        self.mox.ReplayAll()

        form_data = {
            'method': 'CreateOrganizationForm',
            'name': project._info["name"],
            'description': project._info["description"],
        }

        response = self.client.post(CREATE_URL, form_data)
        self.assertNoFormErrors(response)

    def test_create_organization_required_fields(self):
        form_data = {
            'method': 'CreateOrganizationForm',
            'name': '',
            'description': '',
        }

        response = self.client.post(CREATE_URL, form_data)
        self.assertFormError(response, 'form', 'name', ['This field is required.'])
        self.assertNoMessages() 
    

class UpdateInfoTests(BaseOrganizationsTests):

    @test.create_stubs({
        api.keystone: (
            'tenant_update',
            'tenant_get',
        ),
    })
    def test_update_info(self):
        project = self.get_organization()

        updated_project = {"name": 'Updated organization',
                           "description": 'updated organization',
                           "enabled": True,
                           "city": 'Madrid'}

        api.keystone.tenant_get(IsA(http.HttpRequest), project.id).AndReturn(project)
        api.keystone.tenant_update(IsA(http.HttpRequest), 
                                    project.id, 
                                    **updated_project).AndReturn(project)

        self.mox.ReplayAll()

        form_data = {
            'method': 'InfoForm',
            'orgID':project.id,
            'name': updated_project["name"],
            'description': updated_project["description"],
            'city':updated_project["city"],
        }

        url = reverse('horizon:idm:organizations:info', args=[project.id])
        response = self.client.post(url, form_data)
        self.assertNoFormErrors(response)

    @unittest.skip('not ready')
    @test.create_stubs({api.keystone: ('tenant_get',)})
    def test_update_info_required_fields(self):
        project = self.get_organization()

        api.keystone.tenant_get(IsA(http.HttpRequest), project.id).AndReturn(project)
        self.mox.ReplayAll()

        form_data = {
            'method': 'InfoForm',
            'orgID': project.id,
            'name': '',
            'description': '',
            'city': '',
        }

        url = reverse('horizon:idm:organizations:info', args=[project.id])
        response = self.client.post(url, form_data)

        # FIXME(garcianavalon) form contains the last form in forms, not the one
        # we want to test. The world is tought for multiforms :(
        self.assertFormError(response, 'form', 'name', ['This field is required.'])
        self.assertFormError(response, 'form', 'description', ['This field is required.'])
        self.assertNoMessages() 


class UpdateContactTests(BaseOrganizationsTests):


    @test.create_stubs({
        api.keystone: (
            'tenant_update',
            'tenant_get',
        ),
    })
    def test_update_contact(self):
        project = self.get_organization()

        updated_project = {
            "email": 'organization@org.com',
            "website": 'http://www.organization.com/',
        }
        api.keystone.tenant_get(IsA(http.HttpRequest), project.id).AndReturn(project)
        api.keystone.tenant_update(IsA(http.HttpRequest), 
                                    project.id, 
                                    **updated_project).AndReturn(project)

        self.mox.ReplayAll()

        form_data = {
            'method': 'ContactForm',
            'orgID':project.id,
            'email': updated_project["email"],
            'website': updated_project["website"],
        }

        url = reverse('horizon:idm:organizations:contact', args=[project.id])
        response = self.client.post(url, form_data)
        self.assertNoFormErrors(response)

    @test.create_stubs({api.keystone: ('tenant_get',)})
    def test_update_contact_required_fields(self):
        project = self.get_organization()
        api.keystone.tenant_get(IsA(http.HttpRequest), project.id).AndReturn(project)
        self.mox.ReplayAll()

        form_data = {
            'method': 'ContactForm',
            'orgID':project.id,
            'email': '',
            'website': '',
        }

        url = reverse('horizon:idm:organizations:contact', args=[project.id])
        response = self.client.post(url, form_data)
        self.assertNoMessages() 

class DeleteTests(BaseOrganizationsTests):

    @test.create_stubs({
        api.keystone: (
            'tenant_delete',
            'tenant_get',
        ),
    })
    def test_delete_organization(self):
        project = self.get_organization()

        api.keystone.tenant_get(IsA(http.HttpRequest), project.id).AndReturn(project)
        api.keystone.tenant_delete(IsA(http.HttpRequest), project).AndReturn(None)
        self.mox.ReplayAll()

        form_data = {
            'method': 'CancelForm',
            'orgID': project.id,
        }

        url = reverse('horizon:idm:organizations:cancel', args=[project.id])
        response = self.client.post(url, form_data)
        self.assertNoFormErrors(response)

class UpdateAvatarTests(BaseOrganizationsTests):
    # https://docs.djangoproject.com/en/1.7/topics/testing/tools/#django.test.Client.post
    # https://code.google.com/p/pymox/wiki/MoxDocumentation
    @unittest.skip('not ready')
    @test.create_stubs({
        api.keystone: (
            'tenant_update',
        ),
    })
    def test_update_avatar(self):
        project = self.get_organization()

        mock_file = self.mox.CreateMock(file)

        updated_project = {"image": 'image',}

        api.keystone.tenant_update(IsA(http.HttpRequest), 
                                    project.id, 
                                    **updated_project).AndReturn(project)

        self.mox.ReplayAll()

        form_data = {
            'method': 'AvatarForm',
            'orgID':project.id,
            'image': updated_project["image"],  
        }

        url = reverse('horizon:idm:organizations:avatar', args=[project.id])
        response = self.client.post(url, form_data)
        self.assertNoFormErrors(response)

