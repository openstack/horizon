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

from mox import IgnoreArg
from mox import IsA  # noqa

from django import http
from django.contrib import auth as django_auth
from django.core.urlresolvers import reverse

from openstack_auth import exceptions as auth_exceptions
from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

INDEX_URL = reverse('horizon:idm:organizations:index')
CREATE_URL = reverse('horizon:idm:organizations:create')
UPDATE_URL = reverse('horizon:idm:organizations:edit', args=[1])

class OrganizationsTests(test.TestCase):
    # Unit tests for organizations.
    
    # @test.create_stubs({api.keystone: ('tenant_list',)})

    # def test_index(self):
    # 	api.keystone.tenant_list(IsA(http.HttpRequest),
    #                          domain=None,
    #                          paginate=True,
    #                          marker=None) \
    #     .AndReturn([self.tenants.list(), False])
    #     self.mox.ReplayAll()

    #     res = self.client.get(INDEX_URL)
    #     self.assertTemplateUsed(res, 'idm/organizations/index.html')
    #     self.assertItemsEqual(res.context['table'].data, self.tenants.list())

    def _get_project_info(self, project):
        project_info = {"name": unicode(project.name),
                        "description": unicode(project.description),
                        "enabled": project.enabled,
                        "domain": IsA(api.base.APIDictWrapper),
                        "city": '',
                        "email": '',
                        "img":'/static/dashboard/img/logos/small/group.png',
                        "website" : ''}
        return project_info

  
    @test.create_stubs({api.keystone: ('tenant_create',)})

    def test_create_organization(self):
        project = self.tenants.first()
        project_details = self._get_project_info(project)

        api.keystone.tenant_create(IsA(http.HttpRequest), **project_details) \
            .AndReturn(project)


        self.mox.ReplayAll()

        form_data = {
            'method': 'CreateOrganizationForm',
            'name': project._info["name"],
            'description': project._info["description"],
            'enabled': project._info["enabled"]
        }

        response = self.client.post(CREATE_URL, form_data)
        self.assertNoFormErrors(response)

        


    # @test.create_stubs({api.keystone: ('tenant_update',)})
    # def test_update_info(self):
    #     project = self.tenants.first()
    #     project_details = self._get_project_info(project)

    #     updated_project = {"name": 'Updated organization',
    #                        "description": 'updated organization',
    #                        "enabled": project.enabled,
    #                        "city": 'Madrid'}

    #     api.keystone.tenant_update(IsA(http.HttpRequest), project.id, **updated_project) \
    #         .AndReturn(None)

    #     self.mox.ReplayAll()

    #     form_data = {
    #         'method': 'InfoForm',
    #         'orgID':project.id,
    #         'name': updated_project["name"],
    #         'description': updated_project["description"],
    #         'enabled': project._info['enabled'],
    #         'city':updated_project["city"],
    #     }

    #     response = self.client.post(UPDATE_URL, form_data)
    #     self.assertTemplateUsed(response, 'idm/organizations/edit.html')
    #     self.assertNoFormErrors(response)

    # @test.create_stubs({api.keystone: ('tenant_update',)})
    # def test_update_contact(self):
    #     project = self.tenants.first()
    #     project_details = self._get_project_info(project)

    #     updated_project = {"email": 'organization@org.com',
    #                        "website": 'http://www.organization.com',
    #                        }

    #     api.keystone.tenant_update(IsA(http.HttpRequest), project.id, **updated_project) \
    #         .AndReturn(None)

    #     self.mox.ReplayAll()

    #     form_data = {
    #         'method': 'ContactForm',
    #         'orgID':project.id,
    #         'email': updated_project["email"],
    #         'website': updated_project["website"],
    #     }

    #     response = self.client.post(UPDATE_URL, form_data)
    #     self.assertTemplateUsed(res, 'idm/organizations/edit.html')
    #     self.assertNoFormErrors(response)


