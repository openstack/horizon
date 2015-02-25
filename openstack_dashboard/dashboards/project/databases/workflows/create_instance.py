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
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon.utils import memoized
from horizon import workflows
from openstack_dashboard import api

from openstack_dashboard.dashboards.project.instances \
    import utils as instance_utils


LOG = logging.getLogger(__name__)


class SetInstanceDetailsAction(workflows.Action):
    name = forms.CharField(max_length=80, label=_("Instance Name"))
    flavor = forms.ChoiceField(label=_("Flavor"),
                               help_text=_("Size of image to launch."))
    volume = forms.IntegerField(label=_("Volume Size"),
                                min_value=0,
                                initial=1,
                                help_text=_("Size of the volume in GB."))
    datastore = forms.ChoiceField(label=_("Datastore"),
                                  help_text=_(
                                      "Type and version of datastore."))

    class Meta(object):
        name = _("Details")
        help_text_template = "project/databases/_launch_details_help.html"

    def clean(self):
        if self.data.get("datastore", None) == "select_datastore_type_version":
            msg = _("You must select a datastore type and version.")
            self._errors["datastore"] = self.error_class([msg])
        return self.cleaned_data

    @memoized.memoized_method
    def flavors(self, request):
        try:
            return api.trove.flavor_list(request)
        except Exception:
            LOG.exception("Exception while obtaining flavors list")
            redirect = reverse("horizon:project:databases:index")
            exceptions.handle(request,
                              _('Unable to obtain flavors.'),
                              redirect=redirect)

    def populate_flavor_choices(self, request, context):
        flavors = self.flavors(request)
        if flavors:
            return instance_utils.sort_flavor_list(request, flavors)
        return []

    @memoized.memoized_method
    def datastores(self, request):
        try:
            return api.trove.datastore_list(request)
        except Exception:
            LOG.exception("Exception while obtaining datastores list")
            self._datastores = []

    @memoized.memoized_method
    def datastore_versions(self, request, datastore):
        try:
            return api.trove.datastore_version_list(request, datastore)
        except Exception:
            LOG.exception("Exception while obtaining datastore version list")
            self._datastore_versions = []

    def populate_datastore_choices(self, request, context):
        choices = ()
        set_initial = False
        datastores = self.datastores(request)
        if datastores is not None:
            num_datastores_with_one_version = 0
            for ds in datastores:
                versions = self.datastore_versions(request, ds.name)
                if not set_initial:
                    if len(versions) >= 2:
                        set_initial = True
                    elif len(versions) == 1:
                        num_datastores_with_one_version += 1
                        if num_datastores_with_one_version > 1:
                            set_initial = True
                if len(versions) > 0:
                    # only add to choices if datastore has at least one version
                    version_choices = ()
                    for v in versions:
                        version_choices = (version_choices +
                                           ((ds.name + ',' + v.name, v.name),))
                    datastore_choices = (ds.name, version_choices)
                    choices = choices + (datastore_choices,)
            if set_initial:
                # prepend choice to force user to choose
                initial = (('select_datastore_type_version',
                            _('Select datastore type and version')))
                choices = (initial,) + choices
        return choices


TROVE_ADD_USER_PERMS = getattr(settings, 'TROVE_ADD_USER_PERMS', [])
TROVE_ADD_DATABASE_PERMS = getattr(settings, 'TROVE_ADD_DATABASE_PERMS', [])
TROVE_ADD_PERMS = TROVE_ADD_USER_PERMS + TROVE_ADD_DATABASE_PERMS


class SetInstanceDetails(workflows.Step):
    action_class = SetInstanceDetailsAction
    contributes = ("name", "volume", "flavor", "datastore")


class SetNetworkAction(workflows.Action):
    network = forms.MultipleChoiceField(label=_("Networks"),
                                        widget=forms.CheckboxSelectMultiple(),
                                        error_messages={
                                            'required': _(
                                                "At least one network must"
                                                " be specified.")},
                                        help_text=_("Launch instance with"
                                                    " these networks"))

    def __init__(self, request, *args, **kwargs):
        super(SetNetworkAction, self).__init__(request, *args, **kwargs)
        network_list = self.fields["network"].choices
        if len(network_list) == 1:
            self.fields['network'].initial = [network_list[0][0]]

    class Meta(object):
        name = _("Networking")
        permissions = ('openstack.services.network',)
        help_text = _("Select networks for your instance.")

    def populate_network_choices(self, request, context):
        try:
            tenant_id = self.request.user.tenant_id
            networks = api.neutron.network_list_for_tenant(request, tenant_id)
            network_list = [(network.id, network.name_or_id)
                            for network in networks]
        except Exception:
            network_list = []
            exceptions.handle(request,
                              _('Unable to retrieve networks.'))
        return network_list


class SetNetwork(workflows.Step):
    action_class = SetNetworkAction
    template_name = "project/databases/_launch_networks.html"
    contributes = ("network_id",)

    def contribute(self, data, context):
        if data:
            networks = self.workflow.request.POST.getlist("network")
            # If no networks are explicitly specified, network list
            # contains an empty string, so remove it.
            networks = [n for n in networks if n != '']
            if networks:
                context['network_id'] = networks

        return context


class AddDatabasesAction(workflows.Action):
    """Initialize the database with users/databases. This tab will honor
    the settings which should be a list of permissions required:

    * TROVE_ADD_USER_PERMS = []
    * TROVE_ADD_DATABASE_PERMS = []
    """
    databases = forms.CharField(label=_('Initial Databases'),
                                required=False,
                                help_text=_('Comma separated list of '
                                            'databases to create'))
    user = forms.CharField(label=_('Initial Admin User'),
                           required=False,
                           help_text=_("Initial admin user to add"))
    password = forms.CharField(widget=forms.PasswordInput(),
                               label=_("Password"),
                               required=False)
    host = forms.CharField(label=_("Allowed Host (optional)"),
                           required=False,
                           help_text=_("Host or IP that the user is allowed "
                                       "to connect through."))

    class Meta(object):
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


class AdvancedAction(workflows.Action):
    initial_state = forms.ChoiceField(
        label=_('Source for Initial State'),
        required=False,
        help_text=_("Choose initial state."),
        choices=[
            ('', _('None')),
            ('backup', _('Restore from Backup')),
            ('master', _('Replicate from Instance'))],
        widget=forms.Select(attrs={
            'class': 'switchable',
            'data-slug': 'initial_state'
        }))
    backup = forms.ChoiceField(
        label=_('Backup Name'),
        required=False,
        help_text=_('Select a backup to restore'),
        widget=forms.Select(attrs={
            'class': 'switched',
            'data-switch-on': 'initial_state',
            'data-initial_state-backup': _('Backup Name')
        }))
    master = forms.ChoiceField(
        label=_('Master Instance Name'),
        required=False,
        help_text=_('Select a master instance'),
        widget=forms.Select(attrs={
            'class': 'switched',
            'data-switch-on': 'initial_state',
            'data-initial_state-master': _('Master Instance Name')
        }))

    class Meta(object):
        name = _("Advanced")
        help_text_template = "project/databases/_launch_advanced_help.html"

    def populate_backup_choices(self, request, context):
        try:
            backups = api.trove.backup_list(request)
            choices = [(b.id, b.name) for b in backups
                       if b.status == 'COMPLETED']
        except Exception:
            choices = []

        if choices:
            choices.insert(0, ("", _("Select backup")))
        else:
            choices.insert(0, ("", _("No backups available")))
        return choices

    def populate_master_choices(self, request, context):
        try:
            instances = api.trove.instance_list(request)
            choices = [(i.id, i.name) for i in
                       instances if i.status == 'ACTIVE']
        except Exception:
            choices = []

        if choices:
            choices.insert(0, ("", _("Select instance")))
        else:
            choices.insert(0, ("", _("No instances available")))
        return choices

    def clean(self):
        cleaned_data = super(AdvancedAction, self).clean()

        initial_state = cleaned_data.get("initial_state")

        if initial_state == 'backup':
            backup = self.cleaned_data['backup']
            if backup:
                try:
                    bkup = api.trove.backup_get(self.request, backup)
                    self.cleaned_data['backup'] = bkup.id
                except Exception:
                    raise forms.ValidationError(_("Unable to find backup!"))
            else:
                raise forms.ValidationError(_("A backup must be selected!"))

            cleaned_data['master'] = None
        elif initial_state == 'master':
            master = self.cleaned_data['master']
            if master:
                try:
                    api.trove.instance_get(self.request, master)
                except Exception:
                    raise forms.ValidationError(
                        _("Unable to find master instance!"))
            else:
                raise forms.ValidationError(
                    _("A master instance must be selected!"))

            cleaned_data['backup'] = None
        else:
            cleaned_data['master'] = None
            cleaned_data['backup'] = None

        return cleaned_data


class Advanced(workflows.Step):
    action_class = AdvancedAction
    contributes = ['backup', 'master']


class LaunchInstance(workflows.Workflow):
    slug = "launch_instance"
    name = _("Launch Instance")
    finalize_button_name = _("Launch")
    success_message = _('Launched %(count)s named "%(name)s".')
    failure_message = _('Unable to launch %(count)s named "%(name)s".')
    success_url = "horizon:project:databases:index"
    default_steps = (SetInstanceDetails,
                     SetNetwork,
                     InitializeDatabase,
                     Advanced)

    def __init__(self, request=None, context_seed=None, entry_point=None,
                 *args, **kwargs):
        super(LaunchInstance, self).__init__(request, context_seed,
                                             entry_point, *args, **kwargs)
        self.attrs['autocomplete'] = (
            settings.HORIZON_CONFIG.get('password_autocomplete'))

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
                'databases': self._get_databases(context),
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

    def _get_nics(self, context):
        netids = context.get('network_id', None)
        if netids:
            return [{"net-id": netid, "v4-fixed-ip": ""}
                    for netid in netids]
        else:
            return None

    def handle(self, request, context):
        try:
            datastore = self.context['datastore'].split(',')[0]
            datastore_version = self.context['datastore'].split(',')[1]
            LOG.info("Launching database instance with parameters "
                     "{name=%s, volume=%s, flavor=%s, "
                     "datastore=%s, datastore_version=%s, "
                     "dbs=%s, users=%s, "
                     "backups=%s, nics=%s, replica_of=%s}",
                     context['name'], context['volume'], context['flavor'],
                     datastore, datastore_version,
                     self._get_databases(context), self._get_users(context),
                     self._get_backup(context), self._get_nics(context),
                     context.get('master'))
            api.trove.instance_create(request,
                                      context['name'],
                                      context['volume'],
                                      context['flavor'],
                                      datastore=datastore,
                                      datastore_version=datastore_version,
                                      databases=self._get_databases(context),
                                      users=self._get_users(context),
                                      restore_point=self._get_backup(context),
                                      nics=self._get_nics(context),
                                      replica_of=context.get('master'))
            return True
        except Exception:
            exceptions.handle(request)
            return False
