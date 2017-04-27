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
from django.template import defaultfilters as filters
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks \
    import tables as project_tables
from openstack_dashboard import policy

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

    def delete(self, request, obj_id):
        try:
            api.neutron.network_delete(request, obj_id)
        except Exception as e:
            LOG.info('Failed to delete network %(id)s: %(exc)s',
                     {'id': obj_id, 'exc': e})
            msg = _('Failed to delete network %s') % obj_id
            redirect = reverse('horizon:admin:networks:index')
            exceptions.handle(request, msg, redirect=redirect)


class CreateNetwork(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Network")
    url = "horizon:admin:networks:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_network"),)


class EditNetwork(policy.PolicyTargetMixin, tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Network")
    url = "horizon:admin:networks:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("network", "update_network"),)


DISPLAY_CHOICES = (
    ("up", pgettext_lazy("Admin state of a Network", u"UP")),
    ("down", pgettext_lazy("Admin state of a Network", u"DOWN")),
)


class AdminNetworksFilterAction(project_tables.ProjectNetworksFilterAction):
    name = "filter_admin_networks"
    filter_choices = (('project', _("Project ="), True),) +\
        project_tables.ProjectNetworksFilterAction.filter_choices


class NetworksTable(tables.DataTable):
    tenant = tables.Column("tenant_name", verbose_name=_("Project"))
    name = tables.WrappingColumn("name_or_id", verbose_name=_("Network Name"),
                                 link='horizon:admin:networks:detail')
    subnets = tables.Column(project_tables.get_subnets,
                            verbose_name=_("Subnets Associated"),)
    num_agents = tables.Column("num_agents",
                               verbose_name=_("DHCP Agents"))
    shared = tables.Column("shared", verbose_name=_("Shared"),
                           filters=(filters.yesno, filters.capfirst))
    external = tables.Column("router:external",
                             verbose_name=_("External"),
                             filters=(filters.yesno, filters.capfirst))
    status = tables.Column(
        "status", verbose_name=_("Status"),
        display_choices=project_tables.STATUS_DISPLAY_CHOICES)
    admin_state = tables.Column("admin_state",
                                verbose_name=_("Admin State"),
                                display_choices=DISPLAY_CHOICES)

    def get_object_display(self, network):
        return network.name_or_id

    class Meta(object):
        name = "networks"
        verbose_name = _("Networks")
        table_actions = (CreateNetwork, DeleteNetwork,
                         AdminNetworksFilterAction)
        row_actions = (EditNetwork, DeleteNetwork)

    def __init__(self, request, data=None, needs_form_wrapper=None, **kwargs):
        super(NetworksTable, self).__init__(
            request, data=data,
            needs_form_wrapper=needs_form_wrapper,
            **kwargs)
        try:
            if not api.neutron.is_extension_supported(request,
                                                      'dhcp_agent_scheduler'):
                del self.columns['num_agents']
        except Exception:
            msg = _("Unable to check if DHCP agent scheduler "
                    "extension is supported")
            exceptions.handle(self.request, msg)
            del self.columns['num_agents']
