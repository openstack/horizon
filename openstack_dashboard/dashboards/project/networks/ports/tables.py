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
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard import api
from openstack_dashboard import policy
from openstack_dashboard.usage import quotas

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
        base_url = reverse(self.url, args=(network_id, port.id))
        params = {'step': 'update_info'}
        param = urlencode(params)
        return '?'.join([base_url, param])


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

    def allowed(self, request, datum=None):
        usages = quotas.tenant_quota_usages(request, targets=('port', ))
        # when Settings.OPENSTACK_NEUTRON_NETWORK['enable_quotas'] = False
        # usages["port"] is empty
        if usages.get('port', {}).get('available', 1) <= 0:
            if "disabled" not in self.classes:
                self.classes = [c for c in self.classes] + ["disabled"]
                self.verbose_name = _("Create Port (Quota exceeded)")
        else:
            # If the port is deleted, the usage of port will less than
            # the quota again, so we need to redefine the status of the
            # button.
            self.verbose_name = _("Create Port")
            self.classes = [c for c in self.classes if c != "disabled"]

        return True


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
        try:
            api.neutron.port_delete(request, port_id)
        except Exception as e:
            LOG.info('Failed to delete port %(id)s: %(exc)s',
                     {'id': port_id, 'exc': e})
            # NOTE: No exception handling is required here because
            # BatchAction.handle() does it. What we need to do is
            # just to re-raise the exception.
            raise


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
