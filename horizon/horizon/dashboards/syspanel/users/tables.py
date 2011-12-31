import logging

from django import shortcuts
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import tables


LOG = logging.getLogger(__name__)


class CreateUserLink(tables.LinkAction):
    name = "create"
    verbose_name = _("Create User")
    url = "horizon:syspanel:users:create"
    attrs = {
        "class": "ajax-modal btn primary small",
    }


class EditUserLink(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = "horizon:syspanel:users:update"
    attrs = {
        "class": "ajax-modal",
    }


class EnableUsersAction(tables.Action):
    name = "enable"
    verbose_name = _("Enable")
    verbose_name_plural = _("Enable Users")

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


class DeleteUsersAction(tables.Action):
    name = "delete"
    verbose_name = _("Delete")
    verbose_name_plural = _("Delete Users")
    classes = ("danger",)

    def handle(self, data_table, request, object_ids):
        failures = 0
        deleted = []
        for obj_id in object_ids:
            if obj_id == request.user.id:
                messages.info(request, _('You cannot delete the user you are '
                                         'currently logged in as.'))
                continue
            LOG.info('Deleting user with id "%s"' % obj_id)
            try:
                api.keystone.user_delete(request, obj_id)
                deleted.append(obj_id)
            except Exception, e:
                failures += 1
                messages.error(request, _("Error deleting user: %s") % e)
                LOG.exception("Error deleting user.")
        if failures:
            messages.info(request, _("Deleted the following users: %s")
                                     % ", ".join(deleted))
        else:
            if deleted:
                messages.success(request, _("Successfully deleted users: %s")
                                            % ", ".join(deleted))
        return shortcuts.redirect('horizon:syspanel:users:index')


class UserFilterAction(tables.FilterAction):
    def filter(self, table, users, filter_string):
        """ Really naive case-insensitive search. """
        # FIXME(gabriel): This should be smarter. Written for demo purposes.
        q = filter_string.lower()

        def comp(user):
            if q in user.name.lower() or q in user.email.lower():
                return True
            return False

        return filter(comp, users)


class UsersTable(tables.DataTable):
    STATUS_CHOICES = (
        ("true", True),
        ("false", False)
    )
    id = tables.Column(_('id'))
    name = tables.Column(_('name'))
    email = tables.Column(_('email'))
    # Default tenant is not returned from Keystone currently.
    #default_tenant = tables.Column(_('default_tenant'),
    #                               verbose_name="Default Tenant")
    enabled = tables.Column(_('enabled'),
                            status=True,
                            status_choices=STATUS_CHOICES)

    class Meta:
        name = "users"
        verbose_name = _("Users")
        row_actions = (EditUserLink, EnableUsersAction, DisableUsersAction,
                       DeleteUsersAction)
        table_actions = (UserFilterAction, CreateUserLink, DeleteUsersAction)
