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

"""
Views for displaying database backups.
"""
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables as horizon_tables
from horizon.utils import filters
from horizon import views as horizon_views
from horizon import workflows as horizon_workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.database_backups import tables
from openstack_dashboard.dashboards.project.database_backups import workflows


class IndexView(horizon_tables.DataTableView):
    table_class = tables.BackupsTable
    template_name = 'project/database_backups/index.html'
    page_title = _("Backups")

    def _get_extra_data(self, backup):
        """Apply extra info to the backup."""
        instance_id = backup.instance_id
        # TODO(rdopieralski) It's not clear where this attribute is supposed
        # to come from. At first glance it looks like it will always be {}.
        if not hasattr(self, '_instances'):
            self._instances = {}
        instance = self._instances.get(instance_id)
        if instance is None:
            try:
                instance = api.trove.instance_get(self.request, instance_id)
            except Exception:
                instance = _('Not Found')
        backup.instance = instance
        return backup

    def get_data(self):
        # TODO(rmyers) Add pagination support after it is available
        # https://blueprints.launchpad.net/trove/+spec/paginate-backup-list
        try:
            backups = api.trove.backup_list(self.request)
            backups = map(self._get_extra_data, backups)
        except Exception:
            backups = []
            msg = _('Error getting database backup list.')
            exceptions.handle(self.request, msg)
        return backups


class BackupView(horizon_workflows.WorkflowView):
    workflow_class = workflows.CreateBackup
    template_name = "project/database_backups/backup.html"
    page_title = _("Backup Database")

    def get_context_data(self, **kwargs):
        context = super(BackupView, self).get_context_data(**kwargs)
        context["instance_id"] = kwargs.get("instance_id")
        self._instance = context['instance_id']
        return context


class DetailView(horizon_views.APIView):
    template_name = "project/database_backups/details.html"
    page_title = _("Backup Details: {{ backup.name }}")

    def get_data(self, request, context, *args, **kwargs):
        backup_id = kwargs.get("backup_id")
        try:
            backup = api.trove.backup_get(request, backup_id)
            created_at = filters.parse_isotime(backup.created)
            updated_at = filters.parse_isotime(backup.updated)
            backup.duration = updated_at - created_at
        except Exception:
            redirect = reverse('horizon:project:database_backups:index')
            msg = _('Unable to retrieve details for backup: %s') % backup_id
            exceptions.handle(self.request, msg, redirect=redirect)

        try:
            if(hasattr(backup, 'parent_id') and backup.parent_id is not None):
                backup.parent = api.trove.backup_get(request, backup.parent_id)
        except Exception:
            redirect = reverse('horizon:project:database_backups:index')
            msg = (_('Unable to retrieve details for parent backup: %s')
                   % backup.parent_id)
            exceptions.handle(self.request, msg, redirect=redirect)

        try:
            instance = api.trove.instance_get(request, backup.instance_id)
        except Exception:
            instance = None
        context['backup'] = backup
        context['instance'] = instance
        return context
