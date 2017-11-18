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
from django.template import defaultfilters as filters
from django.urls import reverse
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy
from neutronclient.common import exceptions as neutron_exceptions

from horizon import exceptions
from horizon import tables
from horizon.tables import actions

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks.subnets import tables \
    as subnet_tables
from openstack_dashboard import policy
from openstack_dashboard.usage import quotas


LOG = logging.getLogger(__name__)


class DeleteNetwork(policy.PolicyTargetMixin, tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Network",
            u"Delete Networks",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Network",
            u"Deleted Networks",
            count
        )

    policy_rules = (("network", "delete_network"),)

    def allowed(self, request, datum=None):
        if datum and datum.id == api.neutron.AUTO_ALLOCATE_ID:
            return False
        return True

    @actions.handle_exception_with_detail_message(
        # normal_log_message
        'Failed to delete network %(id)s: %(exc)s',
        # target_exception
        neutron_exceptions.Conflict,
        # target_log_message
        'Unable to delete network %(id)s with 409 Conflict: %(exc)s',
        # target_user_message
        _('Unable to delete network %(name)s. Most possible reason is because '
          'one or more ports still exist on the requested network.'),
        # logger_name
        __name__)
    def delete(self, request, network_id):
        network = self.table.get_object_by_id(network_id)
        LOG.debug('Network %(network_id)s has subnets: %(subnets)s',
                  {'network_id': network_id, 'subnets': network.subnets})
        api.neutron.network_delete(request, network_id)
        LOG.debug('Deleted network %s successfully', network_id)


class CreateNetwork(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Network")
    url = "horizon:project:networks:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_network"),)

    def allowed(self, request, datum=None):
        usages = quotas.tenant_quota_usages(request, targets=('network', ))
        # when Settings.OPENSTACK_NEUTRON_NETWORK['enable_quotas'] = False
        # usages["network"] is empty
        if usages.get('network', {}).get('available', 1) <= 0:
            if "disabled" not in self.classes:
                self.classes = [c for c in self.classes] + ["disabled"]
                self.verbose_name = _("Create Network (Quota exceeded)")
        else:
            self.verbose_name = _("Create Network")
            self.classes = [c for c in self.classes if c != "disabled"]

        return True


class EditNetwork(policy.PolicyTargetMixin, tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Network")
    url = "horizon:project:networks:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("network", "update_network"),)

    def allowed(self, request, datum=None):
        if datum and datum.id == api.neutron.AUTO_ALLOCATE_ID:
            return False
        return True


class CreateSubnet(subnet_tables.SubnetPolicyTargetMixin, tables.LinkAction):
    name = "subnet"
    verbose_name = _("Create Subnet")
    url = "horizon:project:networks:createsubnet"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_subnet"),)
    # neutron has used both in their policy files, supporting both
    policy_target_attrs = (("network:tenant_id", "tenant_id"),
                           ("network:project_id", "tenant_id"),)

    def allowed(self, request, datum=None):
        if datum and datum.id == api.neutron.AUTO_ALLOCATE_ID:
            return False
        usages = quotas.tenant_quota_usages(request, targets=('subnet', ))
        # when Settings.OPENSTACK_NEUTRON_NETWORK['enable_quotas'] = False
        # usages["subnet'] is empty
        if usages.get('subnet', {}).get('available', 1) <= 0:
            if 'disabled' not in self.classes:
                self.classes = [c for c in self.classes] + ['disabled']
                self.verbose_name = _('Create Subnet (Quota exceeded)')
        else:
            self.verbose_name = _('Create Subnet')
            self.classes = [c for c in self.classes if c != 'disabled']

        return True


def get_subnets(network):
    template_name = 'project/networks/_network_ips.html'
    context = {"subnets": network.subnets}
    return template.loader.render_to_string(template_name, context)


def get_network_link(network):
    if network.id == api.neutron.AUTO_ALLOCATE_ID:
        return None
    return reverse('horizon:project:networks:detail', args=[network.id])


DISPLAY_CHOICES = (
    ("up", pgettext_lazy("Admin state of a Network", u"UP")),
    ("down", pgettext_lazy("Admin state of a Network", u"DOWN")),
)
STATUS_DISPLAY_CHOICES = (
    ("active", pgettext_lazy("Current status of a Network", u"Active")),
    ("build", pgettext_lazy("Current status of a Network", u"Build")),
    ("down", pgettext_lazy("Current status of a Network", u"Down")),
    ("error", pgettext_lazy("Current status of a Network", u"Error")),
)


def get_availability_zones(network):
    if 'availability_zones' in network and network.availability_zones:
        return ', '.join(network.availability_zones)
    else:
        return _("-")


class ProjectNetworksFilterAction(tables.FilterAction):
    name = "filter_project_networks"
    filter_type = "server"
    filter_choices = (('name', _("Name ="), True),
                      ('shared', _("Shared ="), True,
                       _("e.g. Yes / No")),
                      ('router:external', _("External ="), True,
                       _("e.g. Yes / No")),
                      ('status', _("Status ="), True),
                      ('admin_state_up', _("Admin State ="), True,
                       _("e.g. UP / DOWN")))


class NetworksTable(tables.DataTable):
    name = tables.WrappingColumn("name_or_id",
                                 verbose_name=_("Name"),
                                 link=get_network_link)
    subnets = tables.Column(get_subnets,
                            verbose_name=_("Subnets Associated"),)
    shared = tables.Column("shared", verbose_name=_("Shared"),
                           filters=(filters.yesno, filters.capfirst))
    external = tables.Column("router:external", verbose_name=_("External"),
                             filters=(filters.yesno, filters.capfirst))
    status = tables.Column("status", verbose_name=_("Status"),
                           display_choices=STATUS_DISPLAY_CHOICES)
    admin_state = tables.Column("admin_state",
                                verbose_name=_("Admin State"),
                                display_choices=DISPLAY_CHOICES)
    availability_zones = tables.Column(get_availability_zones,
                                       verbose_name=_("Availability Zones"))

    def __init__(self, request, data=None, needs_form_wrapper=None, **kwargs):
        super(NetworksTable, self).__init__(
            request,
            data=data,
            needs_form_wrapper=needs_form_wrapper,
            **kwargs)
        try:
            if not api.neutron.is_extension_supported(
                    request, "network_availability_zone"):
                del self.columns["availability_zones"]
        except Exception:
            msg = _("Unable to check if network availability zone extension "
                    "is supported")
            exceptions.handle(self.request, msg)
            del self.columns['availability_zones']

    def get_object_display(self, network):
        return network.name_or_id

    class Meta(object):
        name = "networks"
        verbose_name = _("Networks")
        table_actions = (CreateNetwork, DeleteNetwork,
                         ProjectNetworksFilterAction)
        row_actions = (EditNetwork, CreateSubnet, DeleteNetwork)
