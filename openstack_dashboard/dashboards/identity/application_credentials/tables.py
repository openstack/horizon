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

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard import api
from openstack_dashboard import policy

APP_CRED_DETAILS_LINK = "horizon:identity:application_credentials:detail"


class CreateApplicationCredentialLink(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Application Credential")
    url = "horizon:identity:application_credentials:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (('identity', 'identity:create_application_credential'),)


class DeleteApplicationCredentialAction(policy.PolicyTargetMixin,
                                        tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Delete Application Credential",
            "Delete Application Credentials",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Deleted Application Credential",
            "Deleted Application Credentialss",
            count
        )

    policy_rules = (("identity", "identity:delete_application_credential"),)

    def delete(self, request, obj_id):
        api.keystone.application_credential_delete(request, obj_id)


class ApplicationCredentialFilterAction(tables.FilterAction):
    filter_type = "query"
    filter_choices = (("name", _("Application Credential Name ="), True))


def _role_names(obj):
    return [role['name'].encode('utf-8') for role in obj.roles]


class ApplicationCredentialsTable(tables.DataTable):
    name = tables.WrappingColumn('name',
                                 link=APP_CRED_DETAILS_LINK,
                                 verbose_name=_('Name'))
    project_id = tables.Column('project_id', verbose_name=_('Project ID'))
    description = tables.Column('description',
                                verbose_name=_('Description'))
    expires_at = tables.Column('expires_at',
                               verbose_name=_('Expiration'))
    id = tables.Column('id', verbose_name=_('ID'))
    roles = tables.Column(_role_names, verbose_name=_('Roles'))

    class Meta(object):
        name = "application_credentials"
        verbose_name = _("Application Credentials")
        row_actions = (DeleteApplicationCredentialAction,)
        table_actions = (CreateApplicationCredentialLink,
                         DeleteApplicationCredentialAction,
                         ApplicationCredentialFilterAction,)
