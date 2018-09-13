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

from openstack_dashboard.dashboards.identity.groups \
    import tables as groups_tables


class GroupsTable(groups_tables.GroupsTable):
    """Display groups of the project."""
    roles = tables.Column(
        lambda obj: ", ".join(getattr(obj, 'roles', [])),
        verbose_name=_('Roles'),
        form_field=forms.CharField(
            widget=forms.Textarea(attrs={'rows': 4}),
            required=False))

    class Meta(object):
        name = "groupstable"
        verbose_name = _("Groups")
