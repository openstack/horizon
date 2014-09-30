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
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy
from neutronclient.common import exceptions as q_ext

from horizon import exceptions
from horizon import messages
from horizon import tables
from openstack_dashboard import api
from openstack_dashboard import policy

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
        obj = self.table.get_object_by_id(obj_id)
        name = self.table.get_object_display(obj)
        try:
            api.neutron.router_delete(request, obj_id)
        except q_ext.NeutronClientException as e:
            msg = _('Unable to delete router "%s"') % e
            LOG.info(msg)
            messages.error(request, msg)
            redirect = reverse(self.redirect_url)
            raise exceptions.Http302(redirect, message=msg)
        except Exception:
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
        return "-"


class RoutersTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:project:routers:detail")
    status = tables.Column("status",
                           filters=(filters.title,),
                           verbose_name=_("Status"),
                           status=True)
    distributed = tables.Column("distributed",
                                filters=(filters.yesno, filters.capfirst),
                                verbose_name=_("Distributed"))
    ha = tables.Column("ha",
                       filters=(filters.yesno, filters.capfirst),
                       # Translators: High Availability mode of Neutron router
                       verbose_name=_("HA mode"))
    ext_net = tables.Column(get_external_network,
                            verbose_name=_("External Network"))

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

    class Meta:
        name = "Routers"
        verbose_name = _("Routers")
        status_columns = ["status"]
        row_class = UpdateRow
        table_actions = (CreateRouter, DeleteRouter)
        row_actions = (SetGateway, ClearGateway, EditRouter, DeleteRouter)
