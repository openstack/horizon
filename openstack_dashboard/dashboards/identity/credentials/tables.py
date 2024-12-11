# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django import urls
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

from horizon import tables

from openstack_dashboard.api import keystone
from openstack_dashboard import policy


class CreateCredentialAction(tables.LinkAction):
    name = "create"
    verbose_name = _("Create User Credential")
    url = 'horizon:identity:credentials:create'
    classes = ("ajax-modal",)
    policy_rules = (("identity", "identity:create_credential"),)
    icon = "plus"


class UpdateCredentialAction(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit User Credential")
    url = 'horizon:identity:credentials:update'
    classes = ("ajax-modal",)
    policy_rules = (("identity", "identity:update_credential"),)
    icon = "pencil"


class DeleteCredentialAction(tables.DeleteAction):
    help_text = _("Deleted user credentials are not recoverable.")
    policy_rules = (("identity", "identity:delete_credential"),)

    @staticmethod
    def action_present(count):
        return ngettext_lazy(
            "Delete User Credential",
            "Delete User Credentials",
            count
        )

    @staticmethod
    def action_past(count):
        return ngettext_lazy(
            "Deleted User Credential",
            "Deleted User Credentials",
            count
        )

    def delete(self, request, obj_id):
        keystone.credential_delete(request, obj_id)


def get_user_link(datum):
    if datum.user_id is not None:
        return urls.reverse("horizon:identity:users:detail",
                            args=(datum.user_id,))


def get_project_link(datum, request):
    if policy.check((("identity", "identity:get_project"),),
                    request, target={"project": datum}):
        if datum.project_id is not None:
            return urls.reverse("horizon:identity:projects:detail",
                                args=(datum.project_id,))


class CredentialsTable(tables.DataTable):
    user_name = tables.WrappingColumn('user_name',
                                      verbose_name=_('User'),
                                      link=get_user_link)
    cred_type = tables.WrappingColumn('type', verbose_name=_('Type'))
    data = tables.Column('blob', verbose_name=_('Data'))
    project_name = tables.WrappingColumn('project_name',
                                         verbose_name=_('Project'),
                                         link=get_project_link)

    def get_object_id(self, datum):
        """Identifier of the credential."""
        return datum.id

    def get_object_display(self, datum):
        """Display data of the credential."""
        return datum.blob

    class Meta(object):
        name = "credentialstable"
        verbose_name = _("User Credentials")
        table_actions = (CreateCredentialAction,
                         DeleteCredentialAction)
        row_actions = (UpdateCredentialAction,
                       DeleteCredentialAction)
