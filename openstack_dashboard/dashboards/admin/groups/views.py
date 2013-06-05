# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables

from openstack_dashboard import api

from .constants import GROUPS_ADD_MEMBER_AJAX_VIEW_TEMPLATE
from .constants import GROUPS_ADD_MEMBER_VIEW_TEMPLATE
from .constants import GROUPS_CREATE_VIEW_TEMPLATE
from .constants import GROUPS_INDEX_URL
from .constants import GROUPS_INDEX_VIEW_TEMPLATE
from .constants import GROUPS_MANAGE_VIEW_TEMPLATE
from .constants import GROUPS_UPDATE_VIEW_TEMPLATE
from .forms import CreateGroupForm
from .forms import UpdateGroupForm
from .tables import GroupMembersTable
from .tables import GroupNonMembersTable
from .tables import GroupsTable


class IndexView(tables.DataTableView):
    table_class = GroupsTable
    template_name = GROUPS_INDEX_VIEW_TEMPLATE

    def get_data(self):
        groups = []
        domain_context = self.request.session.get('domain_context', None)
        try:
            # TODO(dklyle): once keystoneclient supports filtering by
            # domain change this to use that cleaner method
            groups = api.keystone.group_list(self.request)
            if domain_context:
                domain_groups = []
                for group in groups:
                    if group.domain_id == domain_context:
                        domain_groups.append(group)
                groups = domain_groups
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve group list.'))
        return groups


class CreateView(forms.ModalFormView):
    form_class = CreateGroupForm
    template_name = GROUPS_CREATE_VIEW_TEMPLATE
    success_url = reverse_lazy(GROUPS_INDEX_URL)


class UpdateView(forms.ModalFormView):
    form_class = UpdateGroupForm
    template_name = GROUPS_UPDATE_VIEW_TEMPLATE
    success_url = reverse_lazy(GROUPS_INDEX_URL)

    def get_object(self):
        if not hasattr(self, "_object"):
            try:
                self._object = api.keystone.group_get(self.request,
                                                      self.kwargs['group_id'])
            except:
                redirect = reverse(GROUPS_INDEX_URL)
                exceptions.handle(self.request,
                                  _('Unable to update group.'),
                                  redirect=redirect)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['group'] = self.get_object()
        return context

    def get_initial(self):
        group = self.get_object()
        return {'group_id': group.id,
                'name': group.name,
                'description': group.description}


class GroupManageMixin(object):
    def _get_group(self):
        if not hasattr(self, "_group"):
            group_id = self.kwargs['group_id']
            self._group = api.keystone.group_get(self.request, group_id)
        return self._group

    def _get_group_members(self):
        if not hasattr(self, "_group_members"):
            group_id = self.kwargs['group_id']
            self._group_members = api.keystone.user_list(self.request,
                                                         group=group_id)
        return self._group_members

    def _get_group_non_members(self):
        if not hasattr(self, "_group_non_members"):
            domain_id = self._get_group().domain_id
            all_users = api.keystone.user_list(self.request,
                                               domain=domain_id)
            group_members = self._get_group_members()
            group_member_ids = [user.id for user in group_members]
            self._group_non_members = filter(
                lambda u: u.id not in group_member_ids, all_users)
        return self._group_non_members


class ManageMembersView(GroupManageMixin, tables.DataTableView):
    table_class = GroupMembersTable
    template_name = GROUPS_MANAGE_VIEW_TEMPLATE

    def get_context_data(self, **kwargs):
        context = super(ManageMembersView, self).get_context_data(**kwargs)
        context['group'] = self._get_group()
        return context

    def get_data(self):
        group_members = []
        try:
            group_members = self._get_group_members()
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve group users.'))
        return group_members


class NonMembersView(GroupManageMixin, forms.ModalFormMixin,
                     tables.DataTableView):
    template_name = GROUPS_ADD_MEMBER_VIEW_TEMPLATE
    ajax_template_name = GROUPS_ADD_MEMBER_AJAX_VIEW_TEMPLATE
    table_class = GroupNonMembersTable

    def get_context_data(self, **kwargs):
        context = super(NonMembersView, self).get_context_data(**kwargs)
        context['group'] = self._get_group()
        return context

    def get_data(self):
        group_non_members = []
        try:
            group_non_members = self._get_group_non_members()
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve users.'))
        return group_non_members
