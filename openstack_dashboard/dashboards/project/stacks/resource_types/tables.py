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


class ResourceTypesTable(tables.DataTable):
    class ResourceColumn(tables.Column):
        def get_raw_data(self, datum):
            attr_list = ['implementation', 'component', 'resource']
            info_list = datum.resource_type.split('::')
            info_list[0] = info_list[0].replace("OS", "OpenStack")
            if info_list[0] == "AWS":
                info_list[0] = _("AWS compatible")
            info_dict = dict(zip(attr_list, info_list))
            return info_dict[self.transform]

    name = tables.Column("resource_type",
                         verbose_name=_("Type"),
                         link="horizon:project:stacks.resource_types:details",)
    implementation = ResourceColumn("implementation",
                                    verbose_name=_("Implementation"),)
    component = ResourceColumn("component",
                               verbose_name=_("Component"),)
    resource = ResourceColumn("resource",
                              verbose_name=_("Resource"),)

    def get_object_id(self, resource):
        return resource.resource_type

    class Meta(object):
        name = "resource_types"
        verbose_name = _("Resource Types")
        table_actions = (tables.FilterAction,)
