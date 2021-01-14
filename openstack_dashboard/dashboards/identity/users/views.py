# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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
import operator

from django.conf import settings
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_post_parameters

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard import policy

from openstack_dashboard.dashboards.identity.users \
    import forms as project_forms
from openstack_dashboard.dashboards.identity.users \
    import tables as project_tables
from openstack_dashboard.dashboards.identity.users \
    import tabs as user_tabs
from openstack_dashboard.utils import identity
from openstack_dashboard.utils import settings as setting_utils

LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = project_tables.UsersTable
    template_name = 'identity/users/index.html'
    page_title = _("Users")

    def needs_filter_first(self, table):
        return self._needs_filter_first

    def get_data(self):
        users = []
        filters = self.get_filters()

        self._needs_filter_first = False

        if policy.check((("identity", "identity:list_users"),),
                        self.request):

            # If filter_first is set and if there are not other filters
            # selected, then search criteria must be provided
            # and return an empty list
            if (setting_utils.get_dict_config(
                    'FILTER_DATA_FIRST', 'identity.users') and not filters):
                self._needs_filter_first = True
                return users

            domain_id = identity.get_domain_id_for_operation(self.request)
            try:
                users = api.keystone.user_list(self.request,
                                               domain=domain_id,
                                               filters=filters)
            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to retrieve user list.'))
        elif policy.check((("identity", "identity:get_user"),),
                          self.request):
            try:
                user = api.keystone.user_get(self.request,
                                             self.request.user.id,
                                             admin=False)
                users.append(user)
            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to retrieve user information.'))
        else:
            msg = _("Insufficient privilege level to view user information.")
            messages.info(self.request, msg)

        domain_lookup = api.keystone.domain_lookup(self.request)
        for u in users:
            u.domain_name = domain_lookup.get(u.domain_id)
        return users


class UpdateView(forms.ModalFormView):
    template_name = 'identity/users/update.html'
    form_id = "update_user_form"
    form_class = project_forms.UpdateUserForm
    submit_label = _("Update User")
    submit_url = "horizon:identity:users:update"
    success_url = reverse_lazy('horizon:identity:users:index')
    page_title = _("Update User")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.keystone.user_get(self.request, self.kwargs['user_id'],
                                         admin=True)
        except Exception:
            redirect = reverse("horizon:identity:users:index")
            exceptions.handle(self.request,
                              _('Unable to retrieve user information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        args = (self.kwargs['user_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        user = self.get_object()
        options = getattr(user, "options", {})
        domain_id = getattr(user, "domain_id", None)
        domain_name = ''
        # Retrieve the domain name where the project belongs
        try:
            if policy.check((("identity", "identity:get_domain"),),
                            self.request):
                domain = api.keystone.domain_get(self.request, domain_id)
                domain_name = domain.name

            else:
                domain = api.keystone.get_default_domain(self.request)
                domain_name = domain.get('name')

        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve project domain.'))

        data = {'domain_id': domain_id,
                'domain_name': domain_name,
                'id': user.id,
                'name': user.name,
                'project': user.project_id,
                'email': getattr(user, 'email', None),
                'description': getattr(user, 'description', None),
                'lock_password': options.get("lock_password", False)}
        for key in settings.USER_TABLE_EXTRA_INFO:
            data[key] = getattr(user, key, None)
        return data


class CreateView(forms.ModalFormView):
    template_name = 'identity/users/create.html'
    form_id = "create_user_form"
    form_class = project_forms.CreateUserForm
    submit_label = _("Create User")
    submit_url = reverse_lazy("horizon:identity:users:create")
    success_url = reverse_lazy('horizon:identity:users:index')
    page_title = _("Create User")

    @method_decorator(sensitive_post_parameters('password',
                                                'confirm_password'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        try:
            roles = api.keystone.role_list(self.request)
        except Exception:
            redirect = reverse("horizon:identity:users:index")
            exceptions.handle(self.request,
                              _("Unable to retrieve user roles."),
                              redirect=redirect)
        roles.sort(key=operator.attrgetter("id"))
        kwargs['roles'] = roles
        return kwargs

    def get_initial(self):
        # Set the domain of the user
        domain = api.keystone.get_default_domain(self.request)
        default_role = api.keystone.get_default_role(self.request)
        return {'domain_id': domain.id,
                'domain_name': domain.name,
                'role_id': getattr(default_role, "id", None)}


class DetailView(tabs.TabView):
    tab_group_class = user_tabs.UserDetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ user.name }}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_data()
        table = project_tables.UsersTable(self.request)
        context["user"] = user
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(user)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            user_id = self.kwargs['user_id']
            user = api.keystone.user_get(self.request, user_id, admin=False)
        except Exception:
            redirect = self.get_redirect_url()
            exceptions.handle(self.request,
                              _('Unable to retrieve user details.'),
                              redirect=redirect)
        return user

    def get_redirect_url(self):
        return reverse('horizon:identity:users:index')

    def get_tabs(self, request, *args, **kwargs):
        user = self.get_data()
        return self.tab_group_class(request, user=user, **kwargs)


class ChangePasswordView(forms.ModalFormView):
    template_name = 'identity/users/change_password.html'
    form_id = "change_user_password_form"
    form_class = project_forms.ChangePasswordForm
    submit_url = "horizon:identity:users:change_password"
    submit_label = _("Save")
    success_url = reverse_lazy('horizon:identity:users:index')
    page_title = _("Change Password")

    @method_decorator(sensitive_post_parameters('password',
                                                'confirm_password'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.keystone.user_get(self.request, self.kwargs['user_id'],
                                         admin=False)
        except Exception:
            redirect = reverse("horizon:identity:users:index")
            exceptions.handle(self.request,
                              _('Unable to retrieve user information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        args = (self.kwargs['user_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        user = self.get_object()
        return {'id': self.kwargs['user_id'],
                'name': user.name}
