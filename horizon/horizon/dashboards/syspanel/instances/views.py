# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Openstack, LLC
# Copyright 2012 Nebula, Inc.
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

from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext as _

from horizon import api
from horizon import exceptions
from horizon import tables
from horizon.dashboards.syspanel.instances.tables import SyspanelInstancesTable
from horizon.dashboards.nova.instances_and_volumes \
     .instances.views import console, DetailView, vnc


LOG = logging.getLogger(__name__)


class AdminIndexView(tables.DataTableView):
    table_class = SyspanelInstancesTable
    template_name = 'syspanel/instances/index.html'

    def get_data(self):
        instances = []
        try:
            instances = api.nova.server_list(self.request, all_tenants=True)
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve instance list.'))
        if instances:
            try:
                flavors = api.nova.flavor_list(self.request)
                tenants = SortedDict([(str(tenant.id), tenant) for \
                                      tenant in api.keystone.tenant_list(
                                                    self.request, admin=True)])
                full_flavors = SortedDict([(str(flavor.id), flavor) for \
                                            flavor in flavors])
                for inst in instances:
                    inst.full_flavor = full_flavors[inst.flavor["id"]]
                    inst.internal_identifier = "%s (%s)" % (inst.id,
                                getattr(inst, 'OS-EXT-SRV-ATTR:instance_name'))
                    inst.tenant_name = "%s (%s)" % (inst.tenant_id,
                         tenants[inst.tenant_id].name)
            except:
                msg = _('Unable to retrieve instance size information.')
                exceptions.handle(self.request, msg)
        return instances
