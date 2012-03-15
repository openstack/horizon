import logging

from django import shortcuts
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import tables


LOG = logging.getLogger(__name__)


class CreateUserLink(tables.LinkAction):
    name = "create"
    verbose_name = _("Create User")
    url = "horizon:syspanel:users:create"
    classes = ("ajax-modal", "btn-create")


class EditUserLink(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = "horizon:syspanel:users:update"
    classes = ("ajax-modal", "btn-edit")


class EnableUsersAction(tables.Action):
    name = "enable"
    verbose_name = _("Enable")
    verbose_name_plural = _("Enable Users")
    classes = ("btn-enable",)

    def allowed(self, request, user):
        return not user.enabled

    def handle(self, data_table, request, object_ids):
        failures = 0
        enabled = []
        for obj_id in object_ids:
            try:
                api.keystone.user_update_enabled(request, obj_id, True)
                enabled.append(obj_id)
            except Exception, e:
                failures += 1
                messages.error(request, _("Error enabling user: %s") % e)
                LOG.exception("Error enabling user.")
        if failures:
            messages.info(request, _("Enabled the following users: %s")
                                     % ", ".join(enabled))
        else:
            messages.success(request, _("Successfully enabled users: %s")
                                        % ", ".join(enabled))
        return shortcuts.redirect('horizon:syspanel:users:index')


class DisableUsersAction(tables.Action):
    name = "disable"
    verbose_name = _("Disable")
    verbose_name_plural = _("Disable Users")
    classes = ("btn-disable",)

    def allowed(self, request, user):
        return user.enabled

    def handle(self, data_table, request, object_ids):
        failures = 0
        disabled = []
        for obj_id in object_ids:
            if obj_id == request.user.id:
                messages.info(request, _('You cannot disable the user you are '
                                         'currently logged in as.'))
                continue
            try:
                api.keystone.user_update_enabled(request, obj_id, False)
                disabled.append(obj_id)
            except Exception, e:
                failures += 1
                messages.error(request, _("Error disabling user: %s") % e)
                LOG.exception("Error disabling user.")
        if failures:
            messages.info(request, _("Disabled the following users: %s")
                                     % ", ".join(disabled))
        else:
            if disabled:
                messages.success(request, _("Successfully disabled users: %s")
                                            % ", ".join(disabled))
        return shortcuts.redirect('horizon:syspanel:users:index')


class DeleteUsersAction(tables.DeleteAction):
    data_type_singular = _("User")
    data_type_plural = _("Users")

    def allowed(self, request, datum):
        if datum and datum.id == request.user.id:
            return False
        return True

    def delete(self, request, obj_id):
        api.keystone.user_delete(request, obj_id)


class UserFilterAction(tables.FilterAction):
    def filter(self, table, users, filter_string):
        """ Really naive case-insensitive search. """
        # FIXME(gabriel): This should be smarter. Written for demo purposes.
        q = filter_string.lower()

        def comp(user):
            if any([q in (user.name or "").lower(),
                    q in (user.email or "").lower()]):
                return True
            return False

        return filter(comp, users)


class UsersTable(tables.DataTable):
    STATUS_CHOICES = (
        ("true", True),
        ("false", False)
    )
    id = tables.Column('id', verbose_name=_('ID'))
    name = tables.Column('name', verbose_name=_('User Name'))
    email = tables.Column('email', verbose_name=_('Email'))
    # Default tenant is not returned from Keystone currently.
    #default_tenant = tables.Column('default_tenant',
    #                               verbose_name=_('Default Project'))
    enabled = tables.Column('enabled', verbose_name=_('Enabled'),
                            status=True,
                            status_choices=STATUS_CHOICES)

    class Meta:
        name = "users"
        verbose_name = _("Users")
        if api.keystone_can_edit_user():
            row_actions = (EditUserLink, EnableUsersAction, DisableUsersAction,
                           DeleteUsersAction)
            table_actions = (UserFilterAction, CreateUserLink,
                             DeleteUsersAction)
        else:
            row_actions = (EnableUsersAction, DisableUsersAction)
            table_actions = (UserFilterAction,)
