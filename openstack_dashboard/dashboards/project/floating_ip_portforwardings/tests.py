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
from unittest import mock
import uuid

from django.urls import reverse
from django.utils.http import urlencode

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

from horizon.tables import views as table_views
from horizon.workflows import views

INDEX_URL = reverse('horizon:project:floating_ip_portforwardings:index')
NAMESPACE = "horizon:project:floating_ip_portforwardings"


class FloatingIpPortforwardingViewTests(test.TestCase):

    def setUp(self):
        super().setUp()
        api_mock = mock.patch.object(
            api.neutron,
            'is_extension_floating_ip_port_forwarding_supported').start()
        api_mock.return_value = True

    @test.create_mocks({api.neutron: ('tenant_floating_ip_get',
                                      'floating_ip_port_forwarding_list')})
    def test_floating_ip_portforwarding(self):
        fip = self._get_fip_targets()[0]
        self.mock_tenant_floating_ip_get.return_value = fip
        fip_id = fip.id
        self.mock_floating_ip_port_forwarding_list.return_value = (
            fip.port_forwardings)

        params = urlencode({'floating_ip_id': fip_id})
        url = '?'.join([reverse('%s:show' % NAMESPACE), params])
        res = self.client.get(url)
        self.assertTemplateUsed(res, table_views.DataTableView.template_name)
        table_data = res.context_data['table'].data
        self.assertEqual(len(table_data), 1)
        self.assertEqual(fip.port_forwardings[0].id, table_data[0].id)

    @test.create_mocks({api.neutron: ('floating_ip_port_forwarding_list',
                                      'tenant_floating_ip_list')})
    def test_floating_ip_portforwarding_all(self):
        fips = self._get_fip_targets()
        self.mock_tenant_floating_ip_list.return_value = fips
        fips_dict = {}
        for f in fips:
            fips_dict[f.id] = f.port_forwardings

        def pfw_list(request, fip_id):
            return fips_dict[fip_id]

        self.mock_floating_ip_port_forwarding_list.side_effect = pfw_list

        url = reverse('%s:index' % NAMESPACE)

        res = self.client.get(url)
        self.assertTemplateUsed(res, table_views.DataTableView.template_name)
        table_data = res.context_data['table'].data
        self.assertEqual(len(table_data), len(fips))
        for pfw in table_data:
            self.assertIn(pfw.id, list(map(lambda x: x.id,
                                           fips_dict[pfw.floating_ip_id])))

    def _get_compute_ports(self):
        return [p for p in self.ports.list()
                if not p.device_owner.startswith('network:')]

    def _get_fip_targets(self):
        server_dict = dict((s.id, s.name) for s in self.servers.list())
        targets = []
        port = 10
        for p in self._get_compute_ports():
            for ip in p.fixed_ips:
                targets.append(api.neutron.FloatingIpTarget(
                    p, ip['ip_address'], server_dict.get(p.device_id)))
                targets[-1].ip = ip['ip_address']
                targets[-1].port_id = None
                targets[-1].port_forwardings = [api.neutron.PortForwarding({
                    'id': str(uuid.uuid4()),
                    'floating_ip_id': targets[-1].id,
                    'protocol': 'TCP',
                    'internal_port_range': str(port),
                    'external_port_range': str(port + 10),
                    'internal_ip_address': ip['ip_address'],
                    'description': '',
                    'internal_port_id': '',
                    'external_ip_address': ''}, targets[-1].id)]

                port += 1
        return targets

    @test.create_mocks({api.neutron: ('tenant_floating_ip_get',
                                      'floating_ip_port_forwarding_list',
                                      'floating_ip_target_list')})
    def test_create_floating_ip_portforwarding(self):
        fip = self._get_fip_targets()[0]
        self.mock_tenant_floating_ip_get.return_value = fip
        fip_id = fip.id
        self.mock_floating_ip_port_forwarding_list.return_value = (
            fip.port_forwardings)
        self.mock_floating_ip_target_list.return_value = [fip]

        params = urlencode({'floating_ip_id': fip_id})
        url = '?'.join([reverse('%s:create' % NAMESPACE), params])
        res = self.client.get(url)
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        workflow = res.context['workflow']
        choices = dict(
            workflow.steps[0].action.fields[
                'internal_ip_address'].choices)
        choices.pop('Select an IP-Address')

        self.assertEqual({fip.id}, set(choices.keys()))

    @test.create_mocks({api.neutron: ('tenant_floating_ip_get',
                                      'floating_ip_port_forwarding_list',
                                      'floating_ip_port_forwarding_create',
                                      'floating_ip_target_list')})
    def test_create_floating_ip_portforwarding_post(self):
        fip = self._get_fip_targets()[0]
        self.mock_tenant_floating_ip_get.return_value = fip
        fip_id = fip.id
        self.mock_floating_ip_port_forwarding_list.return_value = (
            fip.port_forwardings)
        self.mock_floating_ip_target_list.return_value = [fip]

        create_mock = self.mock_floating_ip_port_forwarding_create

        params = urlencode({'floating_ip_id': fip_id})
        url = '?'.join([reverse('%s:create' % NAMESPACE), params])
        port = self.ports.get(id=fip.id.split('_')[0])
        internal_ip = '%s_%s' % (port.id, port.fixed_ips[0]['ip_address'])
        post_params = {
            'floating_ip_id': fip_id,
            'description': 'test',
            'internal_port': '10',
            'protocol': 'TCP',
            'internal_ip_address': internal_ip,
            'external_port': '123',
        }
        expected_params = {
            'description': 'test',
            'internal_port': '10',
            'protocol': 'TCP',
            'internal_port_id': internal_ip.split('_')[0],
            'internal_ip_address': internal_ip.split('_')[1],
            'external_port': '123',
        }
        self.client.post(url, post_params)
        create_mock.assert_called_once_with(mock.ANY, fip_id,
                                            **expected_params)

    @test.create_mocks({api.neutron: ('tenant_floating_ip_get',
                                      'floating_ip_port_forwarding_list',
                                      'floating_ip_target_list',
                                      'floating_ip_port_forwarding_get')})
    def test_update_floating_ip_portforwarding(self):
        fip = self._get_fip_targets()[0]
        self.mock_tenant_floating_ip_get.return_value = fip
        fip_id = fip.id
        self.mock_floating_ip_port_forwarding_list.return_value = (
            fip.port_forwardings)
        self.mock_floating_ip_target_list.return_value = [fip]
        self.mock_floating_ip_port_forwarding_get.return_value = {
            'port_forwarding': fip.port_forwardings[0].to_dict()
        }

        params = urlencode({'floating_ip_id': fip_id,
                            'pfwd_id': fip.port_forwardings[0]['id']})
        url = '?'.join([reverse('%s:edit' % NAMESPACE), params])
        res = self.client.get(url)
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        workflow = res.context['workflow']

        self.assertEqual(workflow.steps[0].action.initial['floating_ip_id'],
                         fip.port_forwardings[0]['floating_ip_id'])
        self.assertEqual(workflow.steps[0].action.initial['portforwading_id'],
                         fip.port_forwardings[0]['id'])
        self.assertEqual(workflow.steps[0].action.initial['protocol'],
                         fip.port_forwardings[0]['protocol'])
        self.assertEqual(workflow.steps[0].action.initial['internal_port'],
                         fip.port_forwardings[0]['internal_port_range'])
        self.assertEqual(workflow.steps[0].action.initial['external_port'],
                         fip.port_forwardings[0]['external_port_range'])
        self.assertEqual(workflow.steps[0].action.initial['description'],
                         fip.port_forwardings[0]['description'])

    @test.create_mocks({api.neutron: ('tenant_floating_ip_get',
                                      'floating_ip_port_forwarding_list',
                                      'floating_ip_target_list',
                                      'floating_ip_port_forwarding_update',
                                      'floating_ip_port_forwarding_get')})
    def test_update_floating_ip_portforwarding_post(self):
        fip = self._get_fip_targets()[0]
        self.mock_tenant_floating_ip_get.return_value = fip
        fip_id = fip.id
        self.mock_floating_ip_port_forwarding_list.return_value = (
            fip.port_forwardings)
        self.mock_floating_ip_target_list.return_value = [fip]
        self.mock_floating_ip_port_forwarding_get.return_value = {
            'port_forwarding': fip.port_forwardings[0].to_dict()
        }
        update_mock = self.mock_floating_ip_port_forwarding_update
        pfw_id = fip.port_forwardings[0]['id']
        params = urlencode({'floating_ip_id': fip_id,
                            'pfwd_id': pfw_id})
        url = '?'.join([reverse('%s:edit' % NAMESPACE), params])
        port = self.ports.get(id=fip.id.split('_')[0])
        internal_ip = '%s_%s' % (port.id, port.fixed_ips[0]['ip_address'])

        post_params = {
            'portforwading_id': pfw_id,
            'floating_ip_id': fip_id,
            'description': 'test',
            'internal_port': '10',
            'protocol': 'TCP',
            'internal_ip_address': internal_ip,
            'external_port': '123',
        }
        expected_params = {
            'portforwarding_id': pfw_id,
            'description': 'test',
            'internal_port': '10',
            'protocol': 'TCP',
            'internal_port_id': internal_ip.split('_')[0],
            'internal_ip_address': internal_ip.split('_')[1],
            'external_port': '123',
        }
        self.client.post(url, post_params)
        update_mock.assert_called_once_with(mock.ANY, fip_id,
                                            **expected_params)

    @test.create_mocks({api.neutron: ('tenant_floating_ip_get',
                                      'floating_ip_port_forwarding_list',
                                      'floating_ip_port_forwarding_delete')})
    def test_delete_floating_ip_portforwarding(self):
        fip = self._get_fip_targets()[0]
        self.mock_tenant_floating_ip_get.return_value = fip
        fip_id = fip.id
        self.mock_floating_ip_port_forwarding_list.return_value = (
            fip.port_forwardings)
        deletion_mock = self.mock_floating_ip_port_forwarding_delete
        pf_id = fip.port_forwardings[0].id
        params = urlencode({'floating_ip_id': fip_id})
        url = '?'.join([reverse('%s:show' % NAMESPACE), params])
        self.client.post(url, {
            'action': 'floating_ip_portforwardings__delete__%s' % pf_id})
        deletion_mock.assert_called_once_with(mock.ANY, fip_id, pf_id)
