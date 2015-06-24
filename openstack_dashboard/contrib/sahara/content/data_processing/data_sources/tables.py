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

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard.contrib.sahara.api import sahara as saharaclient

LOG = logging.getLogger(__name__)


class CreateDataSource(tables.LinkAction):
    name = "create data source"
    verbose_name = _("Create Data Source")
    url = "horizon:project:data_processing.data_sources:create-data-source"
    classes = ("ajax-modal",)
    icon = "plus"


class DeleteDataSource(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Data Source",
            u"Delete Data Sources",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Data Source",
            u"Deleted Data Sources",
            count
        )

    def delete(self, request, obj_id):
        saharaclient.data_source_delete(request, obj_id)


class EditDataSource(tables.LinkAction):
    name = "edit data source"
    verbose_name = _("Edit Data Source")
    url = "horizon:project:data_processing.data_sources:edit-data-source"
    classes = ("ajax-modal",)


class DataSourcesTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link=("horizon:project:data_processing."
                               "data_sources:details"))
    type = tables.Column("type",
                         verbose_name=_("Type"))
    description = tables.Column("description",
                                verbose_name=_("Description"))

    class Meta(object):
        name = "data_sources"
        verbose_name = _("Data Sources")
        table_actions = (CreateDataSource,
                         DeleteDataSource)
        row_actions = (DeleteDataSource,
                       EditDataSource,)
