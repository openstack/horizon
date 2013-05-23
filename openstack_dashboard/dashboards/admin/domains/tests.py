# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


from django import http
from django.core.urlresolvers import reverse

from mox import IgnoreArg, IsA

from horizon.workflows.views import WorkflowView

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

from .constants import DOMAINS_INDEX_VIEW_TEMPLATE, \
    DOMAINS_INDEX_URL as index_url, \
    DOMAINS_CREATE_URL as create_url, \
    DOMAINS_UPDATE_URL as update_url
from .workflows import CreateDomain, UpdateDomain


DOMAINS_INDEX_URL = reverse(index_url)
DOMAIN_CREATE_URL = reverse(create_url)
DOMAIN_UPDATE_URL = reverse(update_url, args=[1])


class DomainsViewTests(test.BaseAdminViewTests):
    @test.create_stubs({api.keystone: ('domain_list',)})
    def test_index(self):
        api.keystone.domain_list(IgnoreArg()).AndReturn(self.domains.list())

        self.mox.ReplayAll()

        res = self.client.get(DOMAINS_INDEX_URL)

        self.assertTemplateUsed(res, DOMAINS_INDEX_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, self.domains.list())
        self.assertContains(res, 'Create Domain')
        self.assertContains(res, 'Edit')
        self.assertContains(res, 'Delete Domain')

    @test.create_stubs({api.keystone: ('domain_list',
                                       'keystone_can_edit_domain')})
    def test_index_with_keystone_can_edit_domain_false(self):
        api.keystone.domain_list(IgnoreArg()).AndReturn(self.domains.list())
        api.keystone.keystone_can_edit_domain() \
            .MultipleTimes().AndReturn(False)

        self.mox.ReplayAll()

        res = self.client.get(DOMAINS_INDEX_URL)

        self.assertTemplateUsed(res, DOMAINS_INDEX_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, self.domains.list())
        self.assertNotContains(res, 'Create Domain')
        self.assertNotContains(res, 'Edit')
        self.assertNotContains(res, 'Delete Domain')

    @test.create_stubs({api.keystone: ('domain_list',
                                       'domain_delete')})
    def test_delete_domain(self):
        domain = self.domains.get(id="2")

        api.keystone.domain_list(IgnoreArg()).AndReturn(self.domains.list())
        api.keystone.domain_delete(IgnoreArg(), domain.id)

        self.mox.ReplayAll()

        formData = {'action': 'domains__delete__%s' % domain.id}
        res = self.client.post(DOMAINS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, DOMAINS_INDEX_URL)

    @test.create_stubs({api.keystone: ('domain_list', )})
    def test_delete_with_enabled_domain(self):
        domain = self.domains.get(id="1")

        api.keystone.domain_list(IgnoreArg()).AndReturn(self.domains.list())

        self.mox.ReplayAll()

        formData = {'action': 'domains__delete__%s' % domain.id}
        res = self.client.post(DOMAINS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, DOMAINS_INDEX_URL)
        self.assertMessageCount(error=2)


class CreateDomainWorkflowTests(test.BaseAdminViewTests):
    def _get_domain_info(self, domain):
        domain_info = {"name": domain.name,
                       "description": domain.description,
                       "enabled": domain.enabled}
        return domain_info

    def _get_workflow_data(self, domain):
        domain_info = self._get_domain_info(domain)
        return domain_info

    def test_add_domain_get(self):
        url = reverse('horizon:admin:domains:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, WorkflowView.template_name)

        workflow = res.context['workflow']
        self.assertEqual(res.context['workflow'].name, CreateDomain.name)

        self.assertQuerysetEqual(workflow.steps,
                                 ['<CreateDomainInfo: create_domain>', ])

    @test.create_stubs({api.keystone: ('domain_create', )})
    def test_add_domain_post(self):
        domain = self.domains.get(id="1")

        api.keystone.domain_create(IsA(http.HttpRequest),
                                   description=domain.description,
                                   enabled=domain.enabled,
                                   name=domain.name).AndReturn(domain)

        self.mox.ReplayAll()

        workflow_data = self._get_workflow_data(domain)

        res = self.client.post(DOMAIN_CREATE_URL, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, DOMAINS_INDEX_URL)


class UpdateDomainWorkflowTests(test.BaseAdminViewTests):
    def _get_domain_info(self, domain):
        domain_info = {"domain_id": domain.id,
                       "name": domain.name,
                       "description": domain.description,
                       "enabled": domain.enabled}
        return domain_info

    def _get_workflow_data(self, domain):
        domain_info = self._get_domain_info(domain)
        return domain_info

    @test.create_stubs({api.keystone: ('domain_get', )})
    def test_update_domain_get(self):
        domain = self.domains.get(id="1")

        api.keystone.domain_get(IsA(http.HttpRequest), '1').AndReturn(domain)

        self.mox.ReplayAll()

        res = self.client.get(DOMAIN_UPDATE_URL)

        self.assertTemplateUsed(res, WorkflowView.template_name)

        workflow = res.context['workflow']
        self.assertEqual(res.context['workflow'].name, UpdateDomain.name)

        self.assertQuerysetEqual(workflow.steps,
                                 ['<UpdateDomainInfo: update_domain>', ])

    @test.create_stubs({api.keystone: ('domain_get',
                                       'domain_update')})
    def test_update_domain_post(self):
        domain = self.domains.get(id="1")
        test_description = 'updated description'

        api.keystone.domain_get(IsA(http.HttpRequest), '1').AndReturn(domain)
        api.keystone.domain_update(IsA(http.HttpRequest),
                                   description=test_description,
                                   domain_id=domain.id,
                                   enabled=domain.enabled,
                                   name=domain.name).AndReturn(None)

        self.mox.ReplayAll()

        workflow_data = self._get_workflow_data(domain)
        workflow_data['description'] = test_description

        res = self.client.post(DOMAIN_UPDATE_URL, workflow_data)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(res, DOMAINS_INDEX_URL)
