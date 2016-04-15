# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.template import defaultfilters as filters
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables
from horizon.utils import filters as utils_filters

from openstack_dashboard import api
from openstack_dashboard import policy


class EvacuateHost(tables.LinkAction):
    name = "evacuate"
    verbose_name = _("Evacuate Host")
    url = "horizon:admin:hypervisors:compute:evacuate_host"
    classes = ("ajax-modal", "btn-migrate")
    policy_rules = (("compute", "compute_extension:evacuate"),)

    def __init__(self, **kwargs):
        super(EvacuateHost, self).__init__(**kwargs)
        self.name = kwargs.get('name', self.name)

    def allowed(self, request, instance):
        if not api.nova.extension_supported('AdminActions', request):
            return False

        return self.datum.state == "down"


class DisableService(policy.PolicyTargetMixin, tables.LinkAction):
    name = "disable"
    verbose_name = _("Disable Service")
    url = "horizon:admin:hypervisors:compute:disable_service"
    classes = ("ajax-modal", "btn-confirm")
    policy_rules = (("compute", "compute_extension:services"),)

    def allowed(self, request, service):
        if not api.nova.extension_supported('AdminActions', request):
            return False

        return service.status == "enabled"


class EnableService(policy.PolicyTargetMixin, tables.BatchAction):
    name = "enable"
    policy_rules = (("compute", "compute_extension:services"),)

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Enable Service",
            u"Enable Services",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Enabled Service",
            u"Enabled Services",
            count
        )

    def allowed(self, request, service):
        if not api.nova.extension_supported('AdminActions', request):
            return False

        return service.status == "disabled"

    def action(self, request, obj_id):
        api.nova.service_enable(request, obj_id, 'nova-compute')


class MigrateMaintenanceHost(tables.LinkAction):
    name = "migrate_maintenance"
    policy_rules = (("compute", "compute_extension:admin_actions:migrate"),)
    classes = ('ajax-modal', 'btn-migrate')
    verbose_name = _("Migrate Host")
    url = "horizon:admin:hypervisors:compute:migrate_host"
    action_type = "danger"

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Migrate Host",
            u"Migrate Hosts",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Migrated Host",
            u"Migrated Hosts",
            count
        )

    def allowed(self, request, service):
        if not api.nova.extension_supported('AdminActions', request):
            return False

        return service.status == "disabled"


class ComputeHostFilterAction(tables.FilterAction):
    def filter(self, table, services, filter_string):
        q = filter_string.lower()

        return filter(lambda service: q in service.host.lower(), services)


class ComputeHostTable(tables.DataTable):
    STATUS_CHOICES = (
        ("enabled", True),
        ("disabled", False),
        ("up", True),
        ("down", False),
    )
    STATUS_DISPLAY_CHOICES = (
        ("enabled", pgettext_lazy("Current status of a Hypervisor",
                                  u"Enabled")),
        ("disabled", pgettext_lazy("Current status of a Hypervisor",
                                   u"Disabled")),
        ("up", pgettext_lazy("Current state of a Hypervisor",
                             u"Up")),
        ("down", pgettext_lazy("Current state of a Hypervisor",
                               u"Down")),
    )

    host = tables.Column('host', verbose_name=_('Host'))
    zone = tables.Column('zone', verbose_name=_('Zone'))
    status = tables.Column('status',
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES,
                           verbose_name=_('Status'))
    state = tables.Column('state',
                          status=True,
                          status_choices=STATUS_CHOICES,
                          display_choices=STATUS_DISPLAY_CHOICES,
                          verbose_name=_('State'))
    updated_at = tables.Column('updated_at',
                               verbose_name=_('Updated At'),
                               filters=(utils_filters.parse_isotime,
                                        filters.timesince))

    def get_object_id(self, obj):
        return obj.host

    def get_object_display(self, obj):
        return obj.host

    class Meta(object):
        name = "compute_host"
        verbose_name = _("Compute Host")
        table_actions = (ComputeHostFilterAction,)
        multi_select = False
        row_actions = (
            EvacuateHost,
            DisableService,
            EnableService,
            MigrateMaintenanceHost
        )
