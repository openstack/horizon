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


class ReleaseIP(tables.Action):
    name = "release"
    verbose_name = _("Release IP")
    classes = ('danger',)

    def handle(self, table, request, object_ids):
        released = []
        for obj_id in object_ids:
            LOG.info('Releasing Floating IP "%s".' % obj_id)
            try:
                api.tenant_floating_ip_release(request, obj_id)
                # Floating IP ids are returned from the API as integers
                released.append(table.get_object_by_id(int(obj_id)))
            except novaclient_exceptions.ClientException, e:
                LOG.exception("ClientException in ReleaseFloatingIp")
                messages.error(request, _('Unable to release Floating IP '
                                          'from tenant.'))
        if released:
            messages.info(request,
                          _('Successfully released floating IPs: %s.')
                            % ", ".join([ip.ip for ip in released]))
        return shortcuts.redirect('horizon:nova:access_and_security:index')


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

    class Meta:
        name = "floating_ips"
        verbose_name = _("Floating IPs")
        table_actions = (AllocateIP, ReleaseIP)
        row_actions = (AssociateIP, DisassociateIP, ReleaseIP)
