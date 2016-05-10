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

from django.template import defaultfilters as filters
from django.utils.translation import ugettext_lazy as _

from horizon import tables


class TemplateVersionsTable(tables.DataTable):
    version = tables.Column(
        "version",
        verbose_name=_("Version"),
        link="horizon:project:stacks.template_versions:details",)
    type = tables.Column(
        "type",
        verbose_name=_("Type"),
        filters=(filters.upper,))

    def get_object_id(self, template_versions):
        return template_versions.version

    class Meta(object):
        name = "template_versions"
        verbose_name = _("Template Versions")


class TemplateFunctionsTable(tables.DataTable):
    functions = tables.Column('functions', verbose_name=_("Function"))
    description = tables.Column('description', verbose_name=_("Description"))

    def get_object_id(self, template_functions):
        return template_functions.functions

    class Meta(object):
        name = "template_functions"
        verbose_name = _("Template Functions")
