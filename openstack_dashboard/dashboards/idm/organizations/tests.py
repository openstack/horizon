# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from mox import IsA  # noqa

from django import http
from django.core.urlresolvers import reverse

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

INDEX_URL = reverse('horizon:idm:organizations:index')
CREATE_URL = reverse('horizon:idm:organizations:create')
BUG = 'BUG on https://trello.com/c/0idWSvhv/2-crear-tests-para-todo-lo-que-llevamos'

class BaseOrganizationsTests(test.TestCase):
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
    # @test.create_stubs({api.keystone: ('tenant_list',)})

    # def test_index(self):
    #   api.keystone.tenant_list(IsA(http.HttpRequest),
    #                          domain=None,
    #                          paginate=True,
    #                          marker=None) \
    #     .AndReturn([self.tenants.list(), False])
    #     self.mox.ReplayAll()

    #     res = self.client.get(INDEX_URL)
    #     self.assertTemplateUsed(res, 'idm/organizations/index.html')
    #     self.assertItemsEqual(res.context['table'].data, self.tenants.list())
    pass

class CreateTests(BaseOrganizationsTests):
    @test.create_stubs({api.keystone: ('tenant_create',)})
    def test_create_organization(self):
        project = self.tenants.first()
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
        self.assertFormError(response, 'form', 'description', ['This field is required.'])
        self.assertNoMessages() 
    

class UpdateInfoTests(BaseOrganizationsTests):
    @test.create_stubs({api.keystone: ('tenant_update',)})
    def test_update_info(self):
        project = self.tenants.first()

        updated_project = {"name": 'Updated organization',
                           "description": 'updated organization',
                           "enabled": True,
                           "city": 'Madrid'}

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

    @unittest.skip(BUG)
    def test_update_info_required_fields(self):
        project = self.tenants.first()
        form_data = {
            'method': 'InfoForm',
            'orgID': project.id,
            'name': '',
            'description': '',
            'city': '',
        }

        url = reverse('horizon:idm:organizations:info', args=[project.id])
        response = self.client.post(url, form_data)
        self.assertFormError(response, 'form', 'name', ['This field is required.'])
        self.assertFormError(response, 'form', 'description', ['This field is required.'])
        self.assertNoMessages() 


class UpdateContactTests(BaseOrganizationsTests):
    @test.create_stubs({api.keystone: ('tenant_update',)})
    def test_update_contact(self):
        project = self.tenants.first()

        updated_project = {"email": 'organization@org.com',
                           "website": 'http://www.organization.com/',
                           }

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

    @unittest.skip(BUG)
    def test_update_contact_required_fields(self):
        project = self.tenants.first()

        form_data = {
            'method': 'ContactForm',
            'orgID':'',
            'email': '',
            'website': '',
        }

        url = reverse('horizon:idm:organizations:contact', args=[project.id])
        response = self.client.post(url, form_data)
        self.assertNoMessages() 

class DeleteTests(BaseOrganizationsTests):
    #Test not working: doesn't call tenant_delete in post
    # @test.create_stubs({api.keystone: ('tenant_delete',)})
    # def test_delete_organization(self):
    #     project = self.tenants.first()
    #     project_details = self._get_project_info(project)

    #     api.keystone.tenant_delete(IsA(http.HttpRequest), project.id) \
    #         .AndReturn(None)

    #     self.mox.ReplayAll()

    #     form_data = {
    #         'method': 'CancelForm',
    #         'orgID':project.id,
    #         # 'name': updated_project["name"],
    #     }

    #     url = reverse('horizon:idm:organizations:cancel',
    #                   args=[project.id])
    #     response = self.client.post(url, form_data)
    #     self.assertNoFormErrors(response)
    pass

class UpdateAvatarTests(BaseOrganizationsTests):
    #Test not working: doesn't call tenant_update in post
    # @test.create_stubs({api.keystone: ('tenant_update',)})
    # def test_update_avatar(self):
    #     project = self.tenants.first()
    #     project_details = self._get_project_info(project)

    #     updated_project = {"image": 'image',}

    #     api.keystone.tenant_update(IsA(http.HttpRequest), project.id, **updated_project) \
    #         .AndReturn(project)

    #     self.mox.ReplayAll()

    #     form_data = {
    #         'method': 'AvatarForm',
    #         'orgID':project.id,
    #         'image': updated_project["image"],
    #     }

    #     url = reverse('horizon:idm:organizations:avatar',
    #                   args=[project.id])
    #     response = self.client.post(url, form_data)
    #     self.assertNoFormErrors(response)
    pass

