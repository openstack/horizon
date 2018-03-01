# Copyright 2012,  Nachi Ueno,  NTT MCL,  Inc.
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
from openstack_dashboard import policy
from openstack_dashboard.usage import quotas


LOG = logging.getLogger(__name__)


class DeleteRouter(policy.PolicyTargetMixin, tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Router",
            u"Delete Routers",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Router",
            u"Deleted Routers",
            count
        )

    redirect_url = "horizon:project:routers:index"
    policy_rules = (("network", "delete_router"),)

    @actions.handle_exception_with_detail_message(
        # normal_log_message
        'Failed to delete router %(id)s: %(exc)s',
        # target_exception
        neutron_exceptions.NeutronClientException,
        # target_log_message
        'Unable to delete router %(id)s: %(exc)s',
        # target_user_message
        _('Unable to delete router %(name)s: %(exc)s'),
        # logger_name
        __name__)
    def delete(self, request, obj_id):
        # detach all interfaces before attempting to delete the router
        search_opts = {'device_owner': 'network:router_interface',
                       'device_id': obj_id}
        ports = api.neutron.port_list(request, **search_opts)
        for port in ports:
            api.neutron.router_remove_interface(request, obj_id,
                                                port_id=port.id)
        api.neutron.router_delete(request, obj_id)


class CreateRouter(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Router")
    url = "horizon:project:routers:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_router"),)

    def allowed(self, request, datum=None):
        usages = quotas.tenant_quota_usages(request, targets=('router', ))
        # when Settings.OPENSTACK_NEUTRON_NETWORK['enable_quotas'] = False
        # usages['router'] is empty
        if usages.get('router', {}).get('available', 1) <= 0:
            if "disabled" not in self.classes:
                self.classes = [c for c in self.classes] + ["disabled"]
                self.verbose_name = _("Create Router (Quota exceeded)")
        else:
            self.verbose_name = _("Create Router")
            self.classes = [c for c in self.classes if c != "disabled"]

        return True


class EditRouter(policy.PolicyTargetMixin, tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Router")
    url = "horizon:project:routers:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("network", "update_router"),)


class SetGateway(policy.PolicyTargetMixin, tables.LinkAction):
    name = "setgateway"
    verbose_name = _("Set Gateway")
    url = "horizon:project:routers:setgateway"
    classes = ("ajax-modal",)
    icon = "camera"
    policy_rules = (("network", "update_router"),)

    def allowed(self, request, datum=None):
        if datum.external_gateway_info:
            return False
        return True


class ClearGateway(policy.PolicyTargetMixin, tables.BatchAction):
    help_text = _("You may reset the gateway later by using the"
                  " set gateway action, but the gateway IP may change.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Clear Gateway",
            u"Clear Gateways",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Cleared Gateway",
            u"Cleared Gateways",
            count
        )

    name = "clear"
    classes = ('btn-cleargateway',)
    redirect_url = "horizon:project:routers:index"
    policy_rules = (("network", "update_router"),)
    action_type = "danger"

    @actions.handle_exception_with_detail_message(
        # normal_log_message
        'Unable to clear gateway for router %(id)s: %(exc)s',
        # target_exception
        neutron_exceptions.Conflict,
        # target_log_message
        'Unable to clear gateway for router %(id)s: %(exc)s',
        # target_user_message
        _('Unable to clear gateway for router %(name)s. '
          'Most possible reason is because the gateway is required '
          'by one or more floating IPs'),
        # logger_name
        __name__)
    def action(self, request, obj_id):
        api.neutron.router_remove_gateway(request, obj_id)

    def get_success_url(self, request):
        return reverse(self.redirect_url)

    def allowed(self, request, datum=None):
        if datum.external_gateway_info:
            return True
        return False


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, router_id):
        router = api.neutron.router_get(request, router_id)
        return router


def get_external_network(router):
    if router.external_gateway_info:
        return router.external_gateway_info['network']
    else:
        return _("-")


def get_availability_zones(router):
    if 'availability_zones' in router and router.availability_zones:
        return ', '.join(router.availability_zones)
    else:
        return _("-")


class RoutersFilterAction(tables.FilterAction):
    name = 'filter_project_routers'
    filter_type = 'server'
    filter_choices = (('name', _("Router Name ="), True),
                      ('status', _("Status ="), True),
                      ('admin_state_up', _("Admin State ="), True,
                       _("e.g. UP / DOWN")))


STATUS_DISPLAY_CHOICES = (
    ("active", pgettext_lazy("current status of router", u"Active")),
    ("error", pgettext_lazy("current status of router", u"Error")),
)
ADMIN_STATE_DISPLAY_CHOICES = (
    ("up", pgettext_lazy("Admin state of a Router", u"UP")),
    ("down", pgettext_lazy("Admin state of a Router", u"DOWN")),
)


class RoutersTable(tables.DataTable):
    name = tables.WrappingColumn("name",
                                 verbose_name=_("Name"),
                                 link="horizon:project:routers:detail")
    status = tables.Column("status",
                           verbose_name=_("Status"),
                           status=True,
                           display_choices=STATUS_DISPLAY_CHOICES)
    distributed = tables.Column("distributed",
                                filters=(filters.yesno, filters.capfirst),
                                verbose_name=_("Distributed"))
    ha = tables.Column("ha",
                       filters=(filters.yesno, filters.capfirst),
                       # Translators: High Availability mode of Neutron router
                       verbose_name=_("HA mode"))
    ext_net = tables.Column(get_external_network,
                            verbose_name=_("External Network"))
    admin_state = tables.Column("admin_state",
                                verbose_name=_("Admin State"),
                                display_choices=ADMIN_STATE_DISPLAY_CHOICES)
    availability_zones = tables.Column(get_availability_zones,
                                       verbose_name=_("Availability Zones"))

    def __init__(self, request, data=None, needs_form_wrapper=None, **kwargs):
        super(RoutersTable, self).__init__(
            request,
            data=data,
            needs_form_wrapper=needs_form_wrapper,
            **kwargs)
        if not api.neutron.get_feature_permission(request, "dvr", "get"):
            del self.columns["distributed"]
        if not api.neutron.get_feature_permission(request, "l3-ha", "get"):
            del self.columns["ha"]
        try:
            if not api.neutron.is_extension_supported(
                    request, "router_availability_zone"):
                del self.columns["availability_zones"]
        except Exception:
            msg = _("Unable to check if router availability zone extension "
                    "is supported")
            exceptions.handle(self.request, msg)
            del self.columns['availability_zones']

    def get_object_display(self, obj):
        return obj.name

    class Meta(object):
        name = "routers"
        verbose_name = _("Routers")
        status_columns = ["status"]
        row_class = UpdateRow
        table_actions = (CreateRouter, DeleteRouter,
                         RoutersFilterAction)
        row_actions = (SetGateway, ClearGateway, EditRouter, DeleteRouter)
