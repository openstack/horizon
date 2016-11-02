# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.utils.translation import ugettext_lazy as _

from horizon import tables


class ResourceTypesFilterAction(tables.FilterAction):
    filter_type = 'server'
    filter_choices = (('name', _('Type ='), True, _("Case sensitive")),)


class ResourceTypesTable(tables.DataTable):
    name = tables.Column("resource_type",
                         verbose_name=_("Type"),
                         link="horizon:project:stacks.resource_types:details",)

    def get_object_id(self, resource):
        return resource.resource_type

    class Meta(object):
        name = "resource_types"
        verbose_name = _("Resource Types")
        table_actions = (ResourceTypesFilterAction,)
        multi_select = False
