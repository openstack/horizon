# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Rackspace Hosting
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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.databases \
    import tables as project_tables


LOG = logging.getLogger(__name__)


class BackupDetailsAction(workflows.Action):
    name = forms.CharField(max_length=80, label=_("Name"))
    instance = forms.ChoiceField(label=_("Database Instance"))
    description = forms.CharField(max_length=512, label=_("Description"),
                                  widget=forms.TextInput(),
                                  required=False,
                                  help_text=_("Optional Backup Description"))

    class Meta:
        name = _("Details")
        help_text_template = \
            "project/database_backups/_backup_details_help.html"

    def populate_instance_choices(self, request, context):
        LOG.info("Obtaining list of instances.")
        try:
            instances = api.trove.instance_list(request)
        except Exception:
            instances = []
            msg = _("Unable to list database instance to backup.")
            exceptions.handle(request, msg)
        return [(i.id, i.name) for i in instances
                if i.status in project_tables.ACTIVE_STATES]


class SetBackupDetails(workflows.Step):
    action_class = BackupDetailsAction
    contributes = ["name", "description", "instance"]


class CreateBackup(workflows.Workflow):
    slug = "create_backup"
    name = _("Backup Database")
    finalize_button_name = _("Backup")
    success_message = _('Scheduled backup "%(name)s".')
    failure_message = _('Unable to launch %(count)s named "%(name)s".')
    success_url = "horizon:project:database_backups:index"
    default_steps = [SetBackupDetails]

    def get_initial(self):
        initial = super(CreateBackup, self).get_initial()
        initial['instance_id']

    def format_status_message(self, message):
        name = self.context.get('name', 'unknown instance')
        return message % {"count": _("instance"), "name": name}

    def handle(self, request, context):
        try:
            LOG.info("Creating backup")
            api.trove.backup_create(request,
                                    context['name'],
                                    context['instance'],
                                    context['description'])
            return True
        except Exception:
            LOG.exception("Exception while creating backup")
            msg = _('Error creating database backup.')
            exceptions.handle(request, msg)
            return False
