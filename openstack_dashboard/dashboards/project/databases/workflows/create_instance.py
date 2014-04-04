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

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from horizon import exceptions
from horizon import forms
from horizon.utils import memoized
from horizon import workflows

from openstack_dashboard import api

LOG = logging.getLogger(__name__)


class SetInstanceDetailsAction(workflows.Action):
    name = forms.CharField(max_length=80, label=_("Database Name"))
    flavor = forms.ChoiceField(label=_("Flavor"),
                               help_text=_("Size of image to launch."))
    volume = forms.IntegerField(label=_("Volume Size"),
                                min_value=0,
                                initial=1,
                                help_text=_("Size of the volume in GB."))

    class Meta:
        name = _("Details")
        help_text_template = ("project/databases/_launch_details_help.html")

    @memoized.memoized_method
    def flavors(self, request):
        try:
            return api.trove.flavor_list(request)
        except Exception:
            LOG.exception("Exception while obtaining flavors list")
            self._flavors = []

    def populate_flavor_choices(self, request, context):
        flavor_list = [(f.id, "%s" % f.name) for f in self.flavors(request)]
        return sorted(flavor_list)


TROVE_ADD_USER_PERMS = getattr(settings, 'TROVE_ADD_USER_PERMS', [])
TROVE_ADD_DATABASE_PERMS = getattr(settings, 'TROVE_ADD_DATABASE_PERMS', [])
TROVE_ADD_PERMS = TROVE_ADD_USER_PERMS + TROVE_ADD_DATABASE_PERMS


class SetInstanceDetails(workflows.Step):
    action_class = SetInstanceDetailsAction
    contributes = ("name", "volume", "flavor")


class AddDatabasesAction(workflows.Action):
    """Initialize the database with users/databases. This tab will honor
    the settings which should be a list of permissions required:

    * TROVE_ADD_USER_PERMS = []
    * TROVE_ADD_DATABASE_PERMS = []
    """
    databases = forms.CharField(label=_('Initial Database'),
                                required=False,
                                help_text=_('Comma separated list of '
                                            'databases to create'))
    user = forms.CharField(label=_('Initial Admin User'),
                           required=False,
                           help_text=_("Initial admin user to add"))
    password = forms.CharField(widget=forms.PasswordInput(),
                               label=_("Password"),
                               required=False)
    host = forms.CharField(label=_("Host (optional)"),
                           required=False,
                           help_text=_("Host or IP that the user is allowed "
                                       "to connect through."))

    class Meta:
        name = _("Initialize Databases")
        permissions = TROVE_ADD_PERMS
        help_text_template = "project/databases/_launch_initialize_help.html"

    def clean(self):
        cleaned_data = super(AddDatabasesAction, self).clean()
        if cleaned_data.get('user'):
            if not cleaned_data.get('password'):
                msg = _('You must specify a password if you create a user.')
                self._errors["password"] = self.error_class([msg])
            if not cleaned_data.get('databases'):
                msg = _('You must specify at least one database if '
                        'you create a user.')
                self._errors["databases"] = self.error_class([msg])
        return cleaned_data


class InitializeDatabase(workflows.Step):
    action_class = AddDatabasesAction
    contributes = ["databases", 'user', 'password', 'host']


class RestoreAction(workflows.Action):
    backup = forms.ChoiceField(label=_("Backup"),
                               required=False,
                               help_text=_('Select a backup to restore'))

    class Meta:
        name = _("Restore From Backup")
        permissions = ('openstack.services.object-store',)
        help_text_template = "project/databases/_launch_restore_help.html"

    def populate_backup_choices(self, request, context):
        empty = [('', '-')]
        try:
            backups = api.trove.backup_list(request)
            backup_list = [(b.id, b.name) for b in backups
                           if b.status == 'COMPLETED']
        except Exception:
            backup_list = []
        return empty + backup_list

    def clean_backup(self):
        backup = self.cleaned_data['backup']
        if backup:
            try:
                # Make sure the user is not "hacking" the form
                # and that they have access to this backup_id
                LOG.debug("Obtaining backups")
                bkup = api.trove.backup_get(self.request, backup)
                self.cleaned_data['backup'] = bkup.id
            except Exception:
                raise forms.ValidationError(_("Unable to find backup!"))
        return backup


class RestoreBackup(workflows.Step):
    action_class = RestoreAction
    contributes = ['backup']


class LaunchInstance(workflows.Workflow):
    slug = "launch_database"
    name = _("Launch Database")
    finalize_button_name = _("Launch")
    success_message = _('Launched %(count)s named "%(name)s".')
    failure_message = _('Unable to launch %(count)s named "%(name)s".')
    success_url = "horizon:project:databases:index"
    default_steps = (SetInstanceDetails, InitializeDatabase, RestoreBackup)

    def format_status_message(self, message):
        name = self.context.get('name', 'unknown instance')
        return message % {"count": _("instance"), "name": name}

    def _get_databases(self, context):
        """Returns the initial databases for this instance."""
        databases = None
        if context.get('databases'):
            dbs = context['databases']
            databases = [{'name': d.strip()} for d in dbs.split(',')]
        return databases

    def _get_users(self, context):
        users = None
        if context.get('user'):
            user = {
                'name': context['user'],
                'password': context['password'],
                'databases': self._get_databases(context)
            }
            if context['host']:
                user['host'] = context['host']
            users = [user]
        return users

    def _get_backup(self, context):
        backup = None
        if context.get('backup'):
            backup = {'backupRef': context['backup']}
        return backup

    def handle(self, request, context):
        try:
            LOG.info("Launching instance with parameters "
                     "{name=%s, volume=%s, flavor=%s, dbs=%s, users=%s, "
                     "backups=%s}",
                     context['name'], context['volume'], context['flavor'],
                     self._get_databases(context), self._get_users(context),
                     self._get_backup(context))
            api.trove.instance_create(request,
                                      context['name'],
                                      context['volume'],
                                      context['flavor'],
                                      databases=self._get_databases(context),
                                      users=self._get_users(context),
                                      restore_point=self._get_backup(context))
            return True
        except Exception:
            exceptions.handle(request)
            return False
