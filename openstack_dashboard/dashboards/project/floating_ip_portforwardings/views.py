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

"""
Views for managing floating IPs port forwardings
"""
import logging

from django.utils.translation import gettext_lazy as _

from neutronclient.common import exceptions as neutron_exc

from horizon import exceptions
from horizon import tables
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.floating_ip_portforwardings import (
    tables as project_tables)
from openstack_dashboard.dashboards.project.floating_ip_portforwardings import (
    workflows as project_workflows)

LOG = logging.getLogger(__name__)


class CreateView(workflows.WorkflowView):
    workflow_class = (
        project_workflows.FloatingIpPortForwardingRuleCreationWorkflow)


class EditView(workflows.WorkflowView):
    workflow_class = project_workflows.FloatingIpPortForwardingRuleEditWorkflow


class EditToAllView(workflows.WorkflowView):
    workflow_class = (
        project_workflows.FloatingIpPortForwardingRuleEditWorkflowToAll)


class IndexView(tables.DataTableView):
    table_class = project_tables.FloatingIpPortForwardingRulesTable
    page_title = _("Manage floating IP port forwarding rules")

    def get_data(self):
        try:
            floating_ip_id = self.request.GET.get('floating_ip_id')
            floating_ip = api.neutron.tenant_floating_ip_get(self.request,
                                                             floating_ip_id)
            self.page_title = _(
                "Manage floating IP port forwarding rules : " + str(
                    floating_ip.ip))
            return self.get_floating_ip_rules(floating_ip)
        except neutron_exc.ConnectionFailed:
            exceptions.handle(self.request)
        except Exception:
            exceptions.handle(
                self.request,
                _('Unable to retrieve floating IP port forwarding rules.'))
        return []

    def get_floating_ip_rules(self, floating_ip):
        if floating_ip.port_id:
            return []

        floating_ip_portforwarding_rules = []
        external_ip_address = floating_ip.ip
        floating_ip_id = floating_ip.id
        port_forwarding_rules = api.neutron.floating_ip_port_forwarding_list(
            self.request, floating_ip_id)

        for port_forwarding_rule in port_forwarding_rules:
            setattr(port_forwarding_rule, 'external_ip_address',
                    external_ip_address)

        floating_ip_portforwarding_rules.extend(port_forwarding_rules)

        return floating_ip_portforwarding_rules


class AllRulesView(IndexView):
    table_class = project_tables.AllFloatingIpPortForwardingRulesTable

    def get_data(self):
        try:
            return self.get_all_floating_ip_rules()
        except neutron_exc.ConnectionFailed:
            exceptions.handle(self.request)
        except Exception:
            exceptions.handle(
                self.request,
                _('Unable to retrieve floating IP port forwarding rules.'))
        return []

    def get_all_floating_ip_rules(self):
        floating_ip_portforwarding_rules = []
        floating_ips = api.neutron.tenant_floating_ip_list(self.request)
        for floating_ip in floating_ips:
            floating_ip_portforwarding_rules.extend(
                self.get_floating_ip_rules(floating_ip))

        return floating_ip_portforwarding_rules
