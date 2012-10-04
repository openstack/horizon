# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 NEC Corporation
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

from django import template
from django.utils.translation import ugettext_lazy as _

from horizon import tables


LOG = logging.getLogger(__name__)


def get_fixed_ips(port):
    template_name = 'project/networks/ports/_port_ips.html'
    context = {"ips": port.fixed_ips}
    return template.loader.render_to_string(template_name, context)


def get_attached(port):
    return _('Attached') if port['device_id'] else _('Detached')


class PortsTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:project:networks:ports:detail")
    fixed_ips = tables.Column(get_fixed_ips, verbose_name=_("Fixed IPs"))
    attached = tables.Column(get_attached, verbose_name=_("Device Attached"))
    status = tables.Column("status", verbose_name=_("Status"))
    admin_state = tables.Column("admin_state",
                                verbose_name=_("Admin State"))

    def get_object_display(self, port):
        return port.id

    class Meta:
        name = "ports"
        verbose_name = _("Ports")
