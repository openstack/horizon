# Copyright 2012 OpenStack Foundation
# Copyright 2012 Nebula, Inc.
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

from django.template.defaultfilters import title
from django import urls
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy
from keystoneclient import exceptions as keystone_exceptions

from horizon import tables
from horizon.utils import filters

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.instances import audit_tables
from openstack_dashboard.dashboards.project.instances \
    import tables as project_tables
from openstack_dashboard import policy
from openstack_dashboard.views import get_url_with_pagination


class AdminEditInstance(project_tables.EditInstance):
    url = "horizon:admin:instances:update"


class AdminConsoleLink(project_tables.ConsoleLink):
    url = "horizon:admin:instances:detail"


class AdminLogLink(project_tables.LogLink):
    url = "horizon:admin:instances:detail"


class RescueInstance(project_tables.RescueInstance):
    url = "horizon:admin:instances:rescue"


class MigrateInstance(policy.PolicyTargetMixin, tables.BatchAction):
    name = "migrate"
    classes = ("btn-migrate",)
    policy_rules = (("compute", "os_compute_api:os-migrate-server:migrate"),)
    help_text = _("Migrating instances may cause some unrecoverable results.")
    action_type = "danger"

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Migrate Instance",
            u"Migrate Instances",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled migration (pending confirmation) of Instance",
            u"Scheduled migration (pending confirmation) of Instances",
            count
        )

    def allowed(self, request, instance):
        return ((instance.status in project_tables.ACTIVE_STATES or
                 instance.status == 'SHUTOFF') and
                not project_tables.is_deleting(instance))

    def action(self, request, obj_id):
        api.nova.server_migrate(request, obj_id)


class LiveMigrateInstance(policy.PolicyTargetMixin,
                          tables.LinkAction):
    name = "live_migrate"
    verbose_name = _("Live Migrate Instance")
    url = "horizon:admin:instances:live_migrate"
    classes = ("ajax-modal", "btn-migrate")
    policy_rules = (
        ("compute", "os_compute_api:os-migrate-server:migrate_live"),)

    def allowed(self, request, instance):
        return (instance.status in project_tables.ACTIVE_STATES and
                not project_tables.is_deleting(instance))


class AdminUpdateRow(project_tables.UpdateRow):
    def get_data(self, request, instance_id):
        instance = super(AdminUpdateRow, self).get_data(request, instance_id)
        try:
            tenant = api.keystone.tenant_get(request,
                                             instance.tenant_id,
                                             admin=True)
            instance.tenant_name = getattr(tenant, "name", instance.tenant_id)
        except keystone_exceptions.NotFound:
            instance.tenant_name = None

        return instance


class AdminInstanceFilterAction(tables.FilterAction):
    # Change default name of 'filter' to distinguish this one from the
    # project instances table filter, since this is used as part of the
    # session property used for persisting the filter.
    name = "filter_admin_instances"
    filter_type = "server"
    filter_choices = (
        ('project', _("Project Name ="), True),
        ('tenant_id', _("Project ID ="), True),
        ('host', _("Host Name ="), True),
    ) + project_tables.INSTANCE_FILTER_CHOICES


def get_server_detail_link(obj, request):
    return get_url_with_pagination(
        request, AdminInstancesTable._meta.pagination_param,
        AdminInstancesTable._meta.prev_pagination_param,
        "horizon:admin:instances:detail", obj.id)


class AdminInstancesTable(tables.DataTable):
    TASK_STATUS_CHOICES = (
        (None, True),
        ("none", True)
    )
    STATUS_CHOICES = (
        ("active", True),
        ("shutoff", True),
        ("suspended", True),
        ("paused", True),
        ("error", False),
        ("rescue", True),
        ("shelved", True),
        ("shelved_offloaded", True),
    )
    tenant = tables.Column("tenant_name", verbose_name=_("Project"))
    # NOTE(gabriel): Commenting out the user column because all we have
    # is an ID, and correlating that at production scale using our current
    # techniques isn't practical. It can be added back in when we have names
    # returned in a practical manner by the API.
    # user = tables.Column("user_id", verbose_name=_("User"))
    host = tables.Column("OS-EXT-SRV-ATTR:host",
                         verbose_name=_("Host"),
                         classes=('nowrap-col',))
    name = tables.WrappingColumn("name",
                                 link=get_server_detail_link,
                                 verbose_name=_("Name"))
    image_name = tables.Column("image_name",
                               verbose_name=_("Image Name"))
    ip = tables.Column(project_tables.get_ips,
                       verbose_name=_("IP Address"),
                       attrs={'data-type': "ip"})
    flavor = tables.Column(project_tables.get_flavor,
                           sortable=False,
                           verbose_name=_("Flavor"))
    status = tables.Column(
        "status",
        filters=(title, filters.replace_underscores),
        verbose_name=_("Status"),
        status=True,
        status_choices=STATUS_CHOICES,
        display_choices=project_tables.STATUS_DISPLAY_CHOICES)
    locked = tables.Column(project_tables.render_locked,
                           verbose_name="",
                           sortable=False)
    task = tables.Column("OS-EXT-STS:task_state",
                         verbose_name=_("Task"),
                         empty_value=project_tables.TASK_DISPLAY_NONE,
                         status=True,
                         status_choices=TASK_STATUS_CHOICES,
                         display_choices=project_tables.TASK_DISPLAY_CHOICES)
    state = tables.Column(project_tables.get_power_state,
                          filters=(title, filters.replace_underscores),
                          verbose_name=_("Power State"),
                          display_choices=project_tables.POWER_DISPLAY_CHOICES)
    created = tables.Column("created",
                            verbose_name=_("Age"),
                            filters=(filters.parse_isotime,
                                     filters.timesince_sortable),
                            attrs={'data-type': 'timesince'})

    class Meta(object):
        name = "instances"
        verbose_name = _("Instances")
        status_columns = ["status", "task"]
        table_actions = (project_tables.DeleteInstance,
                         AdminInstanceFilterAction)
        row_class = AdminUpdateRow
        row_actions = (RescueInstance,
                       project_tables.UnRescueInstance,
                       project_tables.ConfirmResize,
                       project_tables.RevertResize,
                       AdminEditInstance,
                       AdminConsoleLink,
                       AdminLogLink,
                       project_tables.CreateSnapshot,
                       project_tables.TogglePause,
                       project_tables.ToggleSuspend,
                       project_tables.ToggleShelve,
                       MigrateInstance,
                       LiveMigrateInstance,
                       project_tables.SoftRebootInstance,
                       project_tables.RebootInstance,
                       project_tables.RebuildInstance,
                       project_tables.StopInstance,
                       project_tables.DeleteInstance)


def user_link(datum):
    return urls.reverse("horizon:identity:users:detail",
                        args=(datum.user_id,))


class AdminAuditTable(audit_tables.AuditTable):
    user_id = tables.Column('user_id', verbose_name=_('User ID'),
                            link=user_link)

    class Meta(object):
        name = 'audit'
        verbose_name = _('Instance Action List')
