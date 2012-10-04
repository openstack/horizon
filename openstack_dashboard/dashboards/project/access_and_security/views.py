# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
# Copyright 2012 OpenStack LLC
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

"""
Views for Instances and Volumes.
"""
import logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api
from .keypairs.tables import KeypairsTable
from .floating_ips.tables import FloatingIPsTable
from .security_groups.tables import SecurityGroupsTable


LOG = logging.getLogger(__name__)


class IndexView(tables.MultiTableView):
    table_classes = (KeypairsTable, SecurityGroupsTable, FloatingIPsTable)
    template_name = 'project/access_and_security/index.html'

    def get_keypairs_data(self):
        try:
            keypairs = api.nova.keypair_list(self.request)
        except:
            keypairs = []
            exceptions.handle(self.request,
                              _('Unable to retrieve keypair list.'))
        return keypairs

    def get_security_groups_data(self):
        try:
            security_groups = api.security_group_list(self.request)
        except:
            security_groups = []
            exceptions.handle(self.request,
                              _('Unable to retrieve security groups.'))
        return security_groups

    def get_floating_ips_data(self):
        try:
            floating_ips = api.tenant_floating_ip_list(self.request)
        except:
            floating_ips = []
            exceptions.handle(self.request,
                              _('Unable to retrieve floating IP addresses.'))

        instances = []
        try:
            instances = api.nova.server_list(self.request, all_tenants=True)
        except:
            exceptions.handle(self.request,
                        _('Unable to retrieve instance list.'))

        instances_dict = dict([(obj.id, obj) for obj in instances])

        for ip in floating_ips:
            ip.instance_name = instances_dict[ip.instance_id].name \
                if ip.instance_id in instances_dict else None

        return floating_ips
