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

from horizon import forms
from horizon import tables

from openstack_dashboard.dashboards.identity.users \
    import tables as users_tables


class UsersTable(users_tables.UsersTable):
    """Display Users of the project with roles."""
    roles = tables.Column(
        lambda obj: ", ".join(getattr(obj, 'roles', [])),
        verbose_name=_('Roles'),
        form_field=forms.CharField(
            widget=forms.Textarea(attrs={'rows': 4}),
            required=False))

    groups_roles = tables.Column(
        lambda obj: ", ".join("%s (%s)" % (role, group) for role, group in
                              getattr(obj, 'roles_from_groups')),
        verbose_name=_('Roles from Groups'),
        form_field=forms.CharField(
            widget=forms.Textarea(attrs={'rows': 4}),
            required=False))

    class Meta(object):
        name = "userstable"
        verbose_name = _("Users")
