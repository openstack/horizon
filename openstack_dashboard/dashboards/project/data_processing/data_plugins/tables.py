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

from horizon import tables

LOG = logging.getLogger(__name__)


class PluginsTable(tables.DataTable):
    title = tables.Column("title",
                          verbose_name=_("Title"),
                          link=("horizon:project:data_processing."
                                "data_plugins:details"))

    versions = tables.Column("versions",
                             verbose_name=_("Supported Versions"),
                             wrap_list=True,
                             filters=(filters.unordered_list,))

    description = tables.Column("description",
                                verbose_name=_("Description"))

    class Meta(object):
        name = "plugins"
        verbose_name = _("Plugins")
