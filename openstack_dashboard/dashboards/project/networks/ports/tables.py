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

from django.core.urlresolvers import reverse
from django import template
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard import policy

LOG = logging.getLogger(__name__)


def get_fixed_ips(port):
    template_name = 'project/networks/ports/_port_ips.html'
    context = {"ips": port.fixed_ips}
    return template.loader.render_to_string(template_name, context)


def get_attached(port):
    if port['device_owner']:
        return port['device_owner']
    elif port['device_id']:
        return _('Attached')
    else:
        return _('Detached')


class UpdatePort(policy.PolicyTargetMixin, tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Port")
    url = "horizon:project:networks:editport"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("network", "update_port"),)

    def get_link_url(self, port):
        network_id = self.table.kwargs['network_id']
        return reverse(self.url, args=(network_id, port.id))


DISPLAY_CHOICES = (
    ("UP", pgettext_lazy("Admin state of a Port", u"UP")),
    ("DOWN", pgettext_lazy("Admin state of a Port", u"DOWN")),
)

STATUS_DISPLAY_CHOICES = (
    ("ACTIVE", pgettext_lazy("status of a network port", u"Active")),
    ("DOWN", pgettext_lazy("status of a network port", u"Down")),
    ("ERROR", pgettext_lazy("status of a network port", u"Error")),
    ("BUILD", pgettext_lazy("status of a network port", u"Build")),
)


class CreatePort(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Port")
    url = "horizon:project:networks:addport"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_port"),)

    def get_link_url(self, datum=None):
        network_id = self.table.kwargs['network_id']
        return reverse(self.url, args=(network_id,))


class DeletePort(policy.PolicyTargetMixin, tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Port",
            u"Delete Ports",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Port",
            u"Deleted Ports",
            count
        )

    policy_rules = (("network", "delete_port"),)

    def delete(self, request, port_id):
        failure_url = "horizon:project:networks:detail"
        try:
            api.neutron.port_delete(request, port_id)
        except Exception as e:
            LOG.info('Failed to delete port %(id)s: %(exc)s',
                     {'id': port_id, 'exc': e})
            msg = _('Failed to delete port %s') % port_id
            network_id = self.table.kwargs['network_id']
            redirect = reverse(failure_url,
                               args=[network_id])
            exceptions.handle(request, msg, redirect=redirect)


class PortsTable(tables.DataTable):
    name = tables.WrappingColumn("name_or_id",
                                 verbose_name=_("Name"),
                                 link="horizon:project:networks:ports:detail")
    fixed_ips = tables.Column(get_fixed_ips, verbose_name=_("Fixed IPs"))
    mac_address = tables.Column("mac_address", verbose_name=_("MAC Address"))
    attached = tables.Column(get_attached, verbose_name=_("Attached Device"))
    status = tables.Column("status",
                           verbose_name=_("Status"),
                           display_choices=STATUS_DISPLAY_CHOICES)
    admin_state = tables.Column("admin_state",
                                verbose_name=_("Admin State"),
                                display_choices=DISPLAY_CHOICES)
    mac_state = tables.Column("mac_state", empty_value=api.neutron.OFF_STATE,
                              verbose_name=_("MAC Learning State"))

    def get_object_display(self, port):
        return port.name_or_id

    class Meta(object):
        name = "ports"
        verbose_name = _("Ports")
        table_actions = (tables.FilterAction, CreatePort, DeletePort)
        row_actions = (UpdatePort, DeletePort)
        hidden_title = False

    def __init__(self, request, data=None, needs_form_wrapper=None, **kwargs):
        super(PortsTable, self).__init__(request, data=data,
                                         needs_form_wrapper=needs_form_wrapper,
                                         **kwargs)
        if not api.neutron.is_extension_supported(request, 'mac-learning'):
            del self.columns['mac_state']
