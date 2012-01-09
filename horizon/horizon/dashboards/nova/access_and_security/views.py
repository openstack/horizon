# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
# Copyright 2011 OpenStack LLC
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

from django.contrib import messages
from django.utils.translation import ugettext as _
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon import tables
from .keypairs.tables import KeypairsTable
from .floating_ips.tables import FloatingIPsTable
from .security_groups.tables import SecurityGroupsTable


LOG = logging.getLogger(__name__)


class IndexView(tables.MultiTableView):
    table_classes = (KeypairsTable, SecurityGroupsTable, FloatingIPsTable)
    template_name = 'nova/access_and_security/index.html'

    def get_keypairs_data(self):
        try:
            keypairs = api.nova.keypair_list(self.request)
        except Exception, e:
            keypairs = []
            LOG.exception("Exception in keypair index")
            messages.error(self.request,
                           _('Keypair list is currently unavailable.'))
        return keypairs

    def get_security_groups_data(self):
        try:
            security_groups = api.security_group_list(self.request)
        except novaclient_exceptions.ClientException, e:
            security_groups = []
            LOG.exception("ClientException in security_groups index")
            messages.error(self.request,
                           _('Error fetching security_groups: %s') % e)
        return security_groups

    def get_floating_ips_data(self):
        try:
            floating_ips = api.tenant_floating_ip_list(self.request)
        except novaclient_exceptions.ClientException, e:
            floating_ips = []
            LOG.exception("ClientException in floating ip index")
            messages.error(self.request,
                        _('Error fetching floating ips: %s') % e)
        return floating_ips
