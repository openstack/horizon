# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 Nebula, Inc.
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

from django import shortcuts
from django.contrib import messages
from django.core.urlresolvers import reverse
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon import tables


LOG = logging.getLogger(__name__)


class AllocateIP(tables.Action):
    name = "allocate"
    verbose_name = _("Allocate IP To Tenant")
    requires_input = False

    def single(self, data_table, request, *args):
        tenant_id = request.user.tenant_id
        try:
            fip = api.tenant_floating_ip_allocate(request)
            LOG.info('Allocating Floating IP "%s" to tenant "%s".'
                     % (fip.ip, tenant_id))
            messages.success(request, _('Successfully allocated Floating IP '
                                        '"%(ip)s" to tenant "%(tenant)s".')
                                        % {"ip": fip.ip, "tenant": tenant_id})
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in FloatingIpAllocate")
            messages.error(request, _('Unable to allocate Floating IP '
                                      '"%(ip)s" to tenant "%(tenant)s".')
                                      % {"ip": fip.ip, "tenant": tenant_id})
        return shortcuts.redirect('horizon:nova:access_and_security:index')


class ReleaseIPs(tables.BatchAction):
    name = "release"
    action_present = _("Release")
    action_past = _("Released")
    data_type_singular = _("Floating IP")
    data_type_plural = _("Floating IPs")

    def action(self, request, obj_id):
        api.tenant_floating_ip_release(request, obj_id)


class AssociateIP(tables.LinkAction):
    name = "associate"
    verbose_name = _("Associate IP")
    url = "horizon:nova:access_and_security:floating_ips:associate"
    attrs = {"class": "ajax-modal"}

    def allowed(self, request, fip):
        if fip.instance_id:
            return False
        return True


class DisassociateIP(tables.Action):
    name = "disassociate"
    verbose_name = _("Disassociate IP")

    def allowed(self, request, fip):
        if fip.instance_id:
            return True
        return False

    def single(self, table, request, obj_id):
        try:
            fip = table.get_object_by_id(int(obj_id))
            api.server_remove_floating_ip(request, fip.instance_id, fip.id)
            LOG.info('Disassociating Floating IP "%s".' % obj_id)
            messages.info(request,
                          _('Successfully disassociated Floating IP: %s')
                          % obj_id)
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in FloatingIpAssociate")
            messages.error(request, _('Error disassociating Floating IP: %s')
                                     % e.message)
        return shortcuts.redirect('horizon:nova:access_and_security:index')


class FloatingIPsTable(tables.DataTable):
    ip = tables.Column("ip", verbose_name=_("IP Address"))
    instance = tables.Column("instance_id",
                             verbose_name=_("Instance"),
                             empty_value="-")

    def sanitize_id(self, obj_id):
        return int(obj_id)

    def get_object_display(self, datum):
        return datum.ip

    class Meta:
        name = "floating_ips"
        verbose_name = _("Floating IPs")
        table_actions = (AllocateIP, ReleaseIPs)
        row_actions = (AssociateIP, DisassociateIP, ReleaseIPs)
