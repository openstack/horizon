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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions

from openstack_dashboard import api
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
                       args=(self.context.get('network_id'),))

    def get_failure_url(self):
        return reverse("horizon:admin:networks:detail",
                       args=(self.context.get('network_id'),))

    def handle(self, request, data):
        try:
            # We must specify tenant_id of the network which a subnet is
            # created for if admin user does not belong to the tenant.
            network = api.neutron.network_get(request,
                                              self.context['network_id'])
        except Exception as e:
            LOG.info('Failed to retrieve network %(id)s for a subnet: %(exc)s',
                     {'id': data['network_id'], 'exc': e})
            msg = (_('Failed to retrieve network %s for a subnet') %
                   data['network_id'])
            redirect = self.get_failure_url()
            exceptions.handle(request, msg, redirect=redirect)
        subnet = self._create_subnet(request, data,
                                     tenant_id=network.tenant_id)
        return True if subnet else False


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
