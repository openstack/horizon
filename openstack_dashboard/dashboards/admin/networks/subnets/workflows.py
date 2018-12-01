# Copyright 2013 NEC Corporation
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

import logging

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from openstack_dashboard.dashboards.project.networks.subnets \
    import workflows as project_workflows
from openstack_dashboard.dashboards.project.networks import workflows \
    as net_workflows


LOG = logging.getLogger(__name__)


class CreateSubnetInfoAction(project_workflows.CreateSubnetInfoAction):
    check_subnet_range = False

    # NOTE(amotoki): As of Newton, workflows.Action does not support
    # an inheritance of django Meta class. It seems subclasses must
    # declare django meta class.
    class Meta(object):
        name = _("Subnet")
        help_text = _('Create a subnet associated with the network. '
                      'Advanced configuration is available by clicking on the '
                      '"Subnet Details" tab.')


class CreateSubnetInfo(project_workflows.CreateSubnetInfo):
    action_class = CreateSubnetInfoAction


class CreateSubnet(project_workflows.CreateSubnet):
    default_steps = (CreateSubnetInfo,
                     net_workflows.CreateSubnetDetail)

    def get_success_url(self):
        return reverse("horizon:admin:networks:detail",
                       args=(self.context['network'].id,))

    def get_failure_url(self):
        return reverse("horizon:admin:networks:detail",
                       args=(self.context['network'].id,))

    def handle(self, request, data):
        network = self.context_seed['network']
        # NOTE: network argument is required to show error message correctly.
        # NOTE: We must specify tenant_id of the network which a subnet is
        # created for if admin user does not belong to the tenant.
        subnet = self._create_subnet(
            request, data,
            network=network,
            tenant_id=network.tenant_id)
        return bool(subnet)


class UpdateSubnetInfoAction(project_workflows.UpdateSubnetInfoAction):
    check_subnet_range = False

    # NOTE(amotoki): As of Newton, workflows.Action does not support
    # an inheritance of django Meta class. It seems subclasses must
    # declare django meta class.
    class Meta(object):
        name = _("Subnet")
        help_text = _('Update a subnet associated with the network. '
                      'Advanced configuration are available at '
                      '"Subnet Details" tab.')


class UpdateSubnetInfo(project_workflows.UpdateSubnetInfo):
    action_class = UpdateSubnetInfoAction


class UpdateSubnet(project_workflows.UpdateSubnet):
    success_url = "horizon:admin:networks:detail"
    failure_url = "horizon:admin:networks:detail"

    default_steps = (UpdateSubnetInfo,
                     project_workflows.UpdateSubnetDetail)
