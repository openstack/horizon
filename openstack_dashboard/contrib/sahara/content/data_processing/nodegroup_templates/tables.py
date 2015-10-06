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

import logging

from django.template import defaultfilters as filters
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables
from openstack_dashboard.contrib.sahara.api import sahara as saharaclient

LOG = logging.getLogger(__name__)


class NodeGroupTemplatesFilterAction(tables.FilterAction):
    filter_type = "server"
    filter_choices = (('name', _("Name"), True),
                      ('plugin_name', _("Plugin"), True),
                      ('hadoop_version', _("Version"), True))


class CreateNodegroupTemplate(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Template")
    url = ("horizon:project:data_processing.nodegroup_templates:"
           "create-nodegroup-template")
    classes = ("ajax-modal", "create-nodegrouptemplate-btn")
    icon = "plus"


class ConfigureNodegroupTemplate(tables.LinkAction):
    name = "configure"
    verbose_name = _("Configure Template")
    url = ("horizon:project:data_processing.nodegroup_templates:"
           "configure-nodegroup-template")
    classes = ("ajax-modal", "configure-nodegrouptemplate-btn")
    icon = "plus"
    attrs = {"style": "display: none"}


class CopyTemplate(tables.LinkAction):
    name = "copy"
    verbose_name = _("Copy Template")
    url = "horizon:project:data_processing.nodegroup_templates:copy"
    classes = ("ajax-modal", )


class EditTemplate(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Template")
    url = "horizon:project:data_processing.nodegroup_templates:edit"
    classes = ("ajax-modal", )


class DeleteTemplate(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Template",
            u"Delete Templates",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Template",
            u"Deleted Templates",
            count
        )

    def delete(self, request, template_id):
        saharaclient.nodegroup_template_delete(request, template_id)


class NodegroupTemplatesTable(tables.DataTable):
    name = tables.Column(
        "name",
        verbose_name=_("Name"),
        link="horizon:project:data_processing.nodegroup_templates:details")
    plugin_name = tables.Column("plugin_name",
                                verbose_name=_("Plugin"))
    hadoop_version = tables.Column("hadoop_version",
                                   verbose_name=_("Version"))
    node_processes = tables.Column("node_processes",
                                   verbose_name=_("Node Processes"),
                                   wrap_list=True,
                                   filters=(filters.unordered_list,))

    class Meta(object):
        name = "nodegroup_templates"
        verbose_name = _("Node Group Templates")
        table_actions = (CreateNodegroupTemplate,
                         ConfigureNodegroupTemplate,
                         DeleteTemplate,
                         NodeGroupTemplatesFilterAction,)
        row_actions = (EditTemplate,
                       CopyTemplate,
                       DeleteTemplate)
