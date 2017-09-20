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
from django.template import defaultfilters as filters
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api
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

    def delete(self, request, network_id):
        network_name = network_id
        try:
            # Retrieve the network list.
            network = api.neutron.network_get(request, network_id,
                                              expand_subnet=False)
            network_name = network.name
            LOG.debug('Network %(network_id)s has subnets: %(subnets)s',
                      {'network_id': network_id, 'subnets': network.subnets})
            for subnet_id in network.subnets:
                api.neutron.subnet_delete(request, subnet_id)
                LOG.debug('Deleted subnet %s', subnet_id)
            api.neutron.network_delete(request, network_id)
            LOG.debug('Deleted network %s successfully', network_id)
        except Exception as e:
            LOG.info('Failed to delete network %(id)s: %(exc)s',
                     {'id': network_id, 'exc': e})
            msg = _('Failed to delete network %s')
            redirect = reverse("horizon:project:networks:index")
            exceptions.handle(request, msg % network_name, redirect=redirect)


class CreateNetwork(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Network")
    url = "horizon:project:networks:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_network"),)

    def allowed(self, request, datum=None):
        usages = quotas.tenant_quota_usages(request, targets=('networks', ))
        # when Settings.OPENSTACK_NEUTRON_NETWORK['enable_quotas'] = False
        # usages["networks"] is empty
        if usages.get('networks', {}).get('available', 1) <= 0:
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


class CreateSubnet(policy.PolicyTargetMixin, tables.LinkAction):
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
        usages = quotas.tenant_quota_usages(request, targets=('subnets', ))
        # when Settings.OPENSTACK_NEUTRON_NETWORK['enable_quotas'] = False
        # usages["subnets'] is empty
        if usages.get('subnets', {}).get('available', 1) <= 0:
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
                                 link='horizon:project:networks:detail')
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

    def get_object_display(self, network):
        return network.name_or_id

    class Meta(object):
        name = "networks"
        verbose_name = _("Networks")
        table_actions = (CreateNetwork, DeleteNetwork,
                         ProjectNetworksFilterAction)
        row_actions = (EditNetwork, CreateSubnet, DeleteNetwork)
