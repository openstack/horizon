# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import operator

from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_post_parameters

from horizon import exceptions
from horizon import forms
from horizon import tables

from openstack_dashboard import api
from .forms import CreateUserForm, UpdateUserForm
from .tables import UsersTable


class IndexView(tables.DataTableView):
    table_class = UsersTable
    template_name = 'admin/users/index.html'

    def get_data(self):
        users = []
        try:
            users = api.keystone.user_list(self.request)
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve user list.'))
        return users


class UpdateView(forms.ModalFormView):
    form_class = UpdateUserForm
    template_name = 'admin/users/update.html'
    success_url = reverse_lazy('horizon:admin:users:index')

    @method_decorator(sensitive_post_parameters('password',
                                                'confirm_password'))
    def dispatch(self, *args, **kwargs):
        return super(UpdateView, self).dispatch(*args, **kwargs)

    def get_object(self):
        if not hasattr(self, "_object"):
            try:
                self._object = api.keystone.user_get(self.request,
                                                     self.kwargs['user_id'],
                                                     admin=True)
            except:
                redirect = reverse("horizon:admin:users:index")
                exceptions.handle(self.request,
                                  _('Unable to update user.'),
                                  redirect=redirect)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['user'] = self.get_object()
        return context

    def get_initial(self):
        user = self.get_object()
        return {'id': user.id,
                'name': user.name,
                'tenant_id': getattr(user, 'tenantId', None),
                'email': user.email}


class CreateView(forms.ModalFormView):
    form_class = CreateUserForm
    template_name = 'admin/users/create.html'
    success_url = reverse_lazy('horizon:admin:users:index')

    @method_decorator(sensitive_post_parameters('password',
                                                'confirm_password'))
    def dispatch(self, *args, **kwargs):
        return super(CreateView, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CreateView, self).get_form_kwargs()
        try:
            roles = api.keystone.role_list(self.request)
        except:
            redirect = reverse("horizon:admin:users:index")
            exceptions.handle(self.request,
                              _("Unable to retrieve user roles."),
                              redirect=redirect)
        roles.sort(key=operator.attrgetter("id"))
        kwargs['roles'] = roles
        return kwargs

    def get_initial(self):
        default_role = api.keystone.get_default_role(self.request)
        return {'role_id': getattr(default_role, "id", None)}
