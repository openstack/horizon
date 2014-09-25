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

from django.core import urlresolvers
from django.http import Http404  # noqa
from django.template.defaultfilters import title  # noqa
from django.utils.http import urlencode  # noqa
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import messages
from horizon import tables
from horizon.utils import filters

from heatclient import exc

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.stacks import mappings


class LaunchStack(tables.LinkAction):
    name = "launch"
    verbose_name = _("Launch Stack")
    url = "horizon:project:stacks:select_template"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("orchestration", "cloudformation:CreateStack"),)


class ChangeStackTemplate(tables.LinkAction):
    name = "edit"
    verbose_name = _("Change Stack Template")
    url = "horizon:project:stacks:change_template"
    classes = ("ajax-modal",)
    icon = "pencil"

    def get_link_url(self, stack):
        return urlresolvers.reverse(self.url, args=[stack.id])


class DeleteStack(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Stack",
            u"Delete Stacks",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Stack",
            u"Deleted Stacks",
            count
        )

    policy_rules = (("orchestration", "cloudformation:DeleteStack"),)

    def delete(self, request, stack_id):
        api.heat.stack_delete(request, stack_id)

    def allowed(self, request, stack):
        if stack is not None:
            return stack.stack_status != 'DELETE_COMPLETE'
        return True


class StacksUpdateRow(tables.Row):
    ajax = True

    def can_be_selected(self, datum):
        return datum.stack_status != 'DELETE_COMPLETE'

    def get_data(self, request, stack_id):
        try:
            return api.heat.stack_get(request, stack_id)
        except exc.HTTPNotFound:
            # returning 404 to the ajax call removes the
            # row from the table on the ui
            raise Http404
        except Exception as e:
            messages.error(request, e)


class StacksTable(tables.DataTable):
    STATUS_CHOICES = (
        ("Complete", True),
        ("Failed", False),
    )
    name = tables.Column("stack_name",
                         verbose_name=_("Stack Name"),
                         link="horizon:project:stacks:detail",)
    created = tables.Column("creation_time",
                            verbose_name=_("Created"),
                            filters=(filters.parse_isotime,
                                     filters.timesince_or_never))
    updated = tables.Column("updated_time",
                            verbose_name=_("Updated"),
                            filters=(filters.parse_isotime,
                                     filters.timesince_or_never))
    status = tables.Column("status",
                           filters=(title, filters.replace_underscores),
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES)

    def get_object_display(self, stack):
        return stack.stack_name

    class Meta:
        name = "stacks"
        verbose_name = _("Stacks")
        pagination_param = 'stack_marker'
        status_columns = ["status", ]
        row_class = StacksUpdateRow
        table_actions = (LaunchStack, DeleteStack,)
        row_actions = (DeleteStack,
                       ChangeStackTemplate)


def get_resource_url(obj):
    return urlresolvers.reverse('horizon:project:stacks:resource',
                                args=(obj.stack_id, obj.resource_name))


class EventsTable(tables.DataTable):

    logical_resource = tables.Column('resource_name',
                                     verbose_name=_("Stack Resource"),
                                     link=get_resource_url)
    physical_resource = tables.Column('physical_resource_id',
                                      verbose_name=_("Resource"),
                                      link=mappings.resource_to_url)
    timestamp = tables.Column('event_time',
                              verbose_name=_("Time Since Event"),
                              filters=(filters.parse_isotime,
                                       filters.timesince_or_never))
    status = tables.Column("resource_status",
                           filters=(title, filters.replace_underscores),
                           verbose_name=_("Status"),)

    statusreason = tables.Column("resource_status_reason",
                                 verbose_name=_("Status Reason"),)

    class Meta:
        name = "events"
        verbose_name = _("Stack Events")


class ResourcesUpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, resource_name):
        try:
            stack = self.table.stack
            stack_identifier = '%s/%s' % (stack.stack_name, stack.id)
            return api.heat.resource_get(
                request, stack_identifier, resource_name)
        except exc.HTTPNotFound:
            # returning 404 to the ajax call removes the
            # row from the table on the ui
            raise Http404
        except Exception as e:
            messages.error(request, e)


class ResourcesTable(tables.DataTable):
    STATUS_CHOICES = (
        ("Create Complete", True),
        ("Create Failed", False),
    )

    logical_resource = tables.Column('resource_name',
                                     verbose_name=_("Stack Resource"),
                                     link=get_resource_url)
    physical_resource = tables.Column('physical_resource_id',
                                     verbose_name=_("Resource"),
                                     link=mappings.resource_to_url)
    resource_type = tables.Column("resource_type",
                           verbose_name=_("Stack Resource Type"),)
    updated_time = tables.Column('updated_time',
                              verbose_name=_("Date Updated"),
                              filters=(filters.parse_isotime,
                                       filters.timesince_or_never))
    status = tables.Column("resource_status",
                           filters=(title, filters.replace_underscores),
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES)

    statusreason = tables.Column("resource_status_reason",
                                 verbose_name=_("Status Reason"),)

    def __init__(self, request, data=None,
                 needs_form_wrapper=None, **kwargs):
        super(ResourcesTable, self).__init__(
            request, data, needs_form_wrapper, **kwargs)
        self.stack = kwargs['stack']

    def get_object_id(self, datum):
        return datum.resource_name

    class Meta:
        name = "resources"
        verbose_name = _("Stack Resources")
        status_columns = ["status", ]
        row_class = ResourcesUpdateRow
