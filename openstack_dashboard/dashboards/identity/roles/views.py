# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import tables
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard import policy

from openstack_dashboard.dashboards.identity.roles \
    import forms as project_forms
from openstack_dashboard.dashboards.identity.roles \
    import tables as project_tables


class IndexView(tables.DataTableView):
    table_class = project_tables.RolesTable
    page_title = _("Roles")

    def needs_filter_first(self, table):
        return self._needs_filter_first

    def get_data(self):
        roles = []
        filters = self.get_filters()

        self._needs_filter_first = False

        if policy.check((("identity", "identity:list_roles"),),
                        self.request):

            # If filter_first is set and if there are not other filters
            # selected, then search criteria must be provided
            # and return an empty list
            filter_first = getattr(settings, 'FILTER_DATA_FIRST', {})
            if filter_first.get('identity.roles', False) and len(filters) == 0:
                self._needs_filter_first = True
                return roles

            try:
                roles = api.keystone.role_list(self.request,
                                               filters=filters)
            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to retrieve roles list.'))
        else:
            msg = _("Insufficient privilege level to view role information.")
            messages.info(self.request, msg)
        return roles


class UpdateView(forms.ModalFormView):
    template_name = 'identity/roles/update.html'
    form_id = "update_role_form"
    form_class = project_forms.UpdateRoleForm
    submit_label = _("Update Role")
    submit_url = "horizon:identity:roles:update"
    success_url = reverse_lazy('horizon:identity:roles:index')
    page_title = _("Update Role")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.keystone.role_get(self.request, self.kwargs['role_id'])
        except Exception:
            redirect = reverse("horizon:identity:roles:index")
            exceptions.handle(self.request,
                              _('Unable to update role.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        args = (self.get_object().id,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        role = self.get_object()
        return {'id': role.id,
                'name': role.name}


class CreateView(forms.ModalFormView):
    template_name = 'identity/roles/create.html'
    form_id = "create_role_form"
    form_class = project_forms.CreateRoleForm
    submit_label = _("Create Role")
    submit_url = reverse_lazy("horizon:identity:roles:create")
    success_url = reverse_lazy('horizon:identity:roles:index')
    page_title = _("Create Role")
