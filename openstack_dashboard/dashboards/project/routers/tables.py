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

from django.core.urlresolvers import reverse
from django.template import defaultfilters as filters
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy
from neutronclient.common import exceptions as q_ext

from horizon import exceptions
from horizon import messages
from horizon import tables

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

    def delete(self, request, obj_id):
        try:
            # detach all interfaces before attempting to delete the router
            search_opts = {'device_owner': 'network:router_interface',
                           'device_id': obj_id}
            ports = api.neutron.port_list(request, **search_opts)
            for port in ports:
                api.neutron.router_remove_interface(request, obj_id,
                                                    port_id=port.id)
            api.neutron.router_delete(request, obj_id)
        except q_ext.NeutronClientException as e:
            msg = _('Unable to delete router "%s"') % e
            LOG.info(msg)
            messages.error(request, msg)
            redirect = reverse(self.redirect_url)
            raise exceptions.Http302(redirect, message=msg)
        except Exception:
            obj = self.table.get_object_by_id(obj_id)
            name = self.table.get_object_display(obj)
            msg = _('Unable to delete router "%s"') % name
            LOG.info(msg)
            exceptions.handle(request, msg)

    def allowed(self, request, router=None):
        return True


class CreateRouter(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Router")
    url = "horizon:project:routers:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_router"),)

    def allowed(self, request, datum=None):
        usages = quotas.tenant_quota_usages(request)
        # when Settings.OPENSTACK_NEUTRON_NETWORK['enable_quotas'] = False
        # usages['routers'] is empty
        if usages.get('routers', {}).get('available', 1) <= 0:
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

    name = "cleargateway"
    classes = ('btn-danger', 'btn-cleargateway')
    redirect_url = "horizon:project:routers:index"
    policy_rules = (("network", "update_router"),)

    def action(self, request, obj_id):
        obj = self.table.get_object_by_id(obj_id)
        name = self.table.get_object_display(obj)
        try:
            api.neutron.router_remove_gateway(request, obj_id)
        except Exception as e:
            msg = (_('Unable to clear gateway for router '
                     '"%(name)s": "%(msg)s"')
                   % {"name": name, "msg": e})
            LOG.info(msg)
            redirect = reverse(self.redirect_url)
            exceptions.handle(request, msg, redirect=redirect)

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


class RoutersFilterAction(tables.FilterAction):

    def filter(self, table, routers, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [router for router in routers
                if query in router.name.lower()]


class RoutersTable(tables.DataTable):
    STATUS_DISPLAY_CHOICES = (
        ("active", pgettext_lazy("current status of router", u"Active")),
        ("error", pgettext_lazy("current status of router", u"Error")),
    )
    ADMIN_STATE_DISPLAY_CHOICES = (
        ("UP", pgettext_lazy("Admin state of a Router", u"UP")),
        ("DOWN", pgettext_lazy("Admin state of a Router", u"DOWN")),
    )

    name = tables.Column("name",
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

    def get_object_display(self, obj):
        return obj.name

    class Meta(object):
        name = "Routers"
        verbose_name = _("Routers")
        status_columns = ["status"]
        row_class = UpdateRow
        table_actions = (CreateRouter, DeleteRouter,
                         RoutersFilterAction)
        row_actions = (SetGateway, ClearGateway, EditRouter, DeleteRouter)
