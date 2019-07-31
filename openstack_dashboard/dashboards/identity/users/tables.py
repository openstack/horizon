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

from django.template import defaultfilters
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import forms
from horizon import tables
from openstack_dashboard import api
from openstack_dashboard import policy

ENABLE = 0
DISABLE = 1


class CreateUserLink(tables.LinkAction):
    name = "create"
    verbose_name = _("Create User")
    url = "horizon:identity:users:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (('identity', 'identity:create_grant'),
                    ("identity", "identity:create_user"),
                    ("identity", "identity:list_roles"),
                    ("identity", "identity:list_projects"),)

    def allowed(self, request, user):
        return api.keystone.keystone_can_edit_user()


class EditUserLink(policy.PolicyTargetMixin, tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = "horizon:identity:users:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("identity", "identity:update_user"),
                    ("identity", "identity:list_projects"),)
    policy_target_attrs = (("user_id", "id"),
                           ("target.user.domain_id", "domain_id"),)

    def allowed(self, request, user):
        return api.keystone.keystone_can_edit_user()


class ChangePasswordLink(policy.PolicyTargetMixin, tables.LinkAction):
    name = "change_password"
    verbose_name = _("Change Password")
    url = "horizon:identity:users:change_password"
    classes = ("ajax-modal",)
    icon = "key"
    policy_rules = (("identity", "identity:update_user"),)
    policy_target_attrs = (("user_id", "id"),
                           ("target.user.domain_id", "domain_id"))

    def allowed(self, request, user):
        return api.keystone.keystone_can_edit_user()


class ToggleEnabled(policy.PolicyTargetMixin, tables.BatchAction):
    name = "toggle"

    @staticmethod
    def action_present(count):
        return (
            ungettext_lazy(
                u"Enable User",
                u"Enable Users",
                count
            ),
            ungettext_lazy(
                u"Disable User",
                u"Disable Users",
                count
            ),
        )

    @staticmethod
    def action_past(count):
        return (
            ungettext_lazy(
                u"Enabled User",
                u"Enabled Users",
                count
            ),
            ungettext_lazy(
                u"Disabled User",
                u"Disabled Users",
                count
            ),
        )
    classes = ("btn-toggle",)
    policy_rules = (("identity", "identity:update_user"),)
    policy_target_attrs = (("user_id", "id"),
                           ("target.user.domain_id", "domain_id"))

    def allowed(self, request, user=None):
        if (not api.keystone.keystone_can_edit_user() or
                user.id == request.user.id):
            return False

        self.enabled = True
        if not user:
            return self.enabled
        self.enabled = user.enabled
        if self.enabled:
            self.current_present_action = DISABLE
        else:
            self.current_present_action = ENABLE
        return True

    def action(self, request, obj_id):
        if self.enabled:
            api.keystone.user_update_enabled(request, obj_id, False)
            self.current_past_action = DISABLE
        else:
            api.keystone.user_update_enabled(request, obj_id, True)
            self.current_past_action = ENABLE


class DeleteUsersAction(policy.PolicyTargetMixin, tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete User",
            u"Delete Users",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted User",
            u"Deleted Users",
            count
        )
    policy_rules = (("identity", "identity:delete_user"),)

    def allowed(self, request, datum):
        if not api.keystone.keystone_can_edit_user() or \
                (datum and datum.id == request.user.id):
            return False
        return True

    def delete(self, request, obj_id):
        api.keystone.user_delete(request, obj_id)


class UserFilterAction(tables.FilterAction):
    if api.keystone.VERSIONS.active < 3:
        filter_type = "query"
    else:
        filter_type = "server"
        filter_choices = (("name", _("User Name ="), True),
                          ("id", _("User ID ="), True),
                          ("enabled", _("Enabled ="), True, _('e.g. Yes/No')))


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, user_id):
        user_info = api.keystone.user_get(request, user_id, admin=True)
        return user_info


class UsersTable(tables.DataTable):
    STATUS_CHOICES = (
        ("true", True),
        ("false", False)
    )
    name = tables.WrappingColumn('name',
                                 link="horizon:identity:users:detail",
                                 verbose_name=_('User Name'),
                                 form_field=forms.CharField(required=False))
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'),
                                form_field=forms.CharField(
                                    widget=forms.Textarea(attrs={'rows': 4}),
                                    required=False))
    email = tables.Column(lambda obj: getattr(obj, 'email', None),
                          verbose_name=_('Email'),
                          form_field=forms.EmailField(required=False),
                          filters=(lambda v: defaultfilters
                                   .default_if_none(v, ""),
                                   defaultfilters.escape,
                                   defaultfilters.urlize)
                          )
    # Default tenant is not returned from Keystone currently.
    # default_tenant = tables.Column('default_tenant',
    #                                verbose_name=_('Default Project'))
    id = tables.Column('id', verbose_name=_('User ID'),
                       attrs={'data-type': 'uuid'})
    enabled = tables.Column('enabled', verbose_name=_('Enabled'),
                            status=True,
                            status_choices=STATUS_CHOICES,
                            filters=(defaultfilters.yesno,
                                     defaultfilters.capfirst),
                            empty_value="False")

    if api.keystone.VERSIONS.active >= 3:
        domain_name = tables.Column('domain_name',
                                    verbose_name=_('Domain Name'),
                                    attrs={'data-type': 'uuid'})

    class Meta(object):
        name = "users"
        verbose_name = _("Users")
        row_actions = (EditUserLink, ChangePasswordLink, ToggleEnabled,
                       DeleteUsersAction)
        table_actions = (UserFilterAction, CreateUserLink, DeleteUsersAction)
        row_class = UpdateRow
