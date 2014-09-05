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

from django.template import defaultfilters as filters
from django.utils.translation import ugettext_lazy as _

from horizon import tables


def render_spec_keys(qos_spec):
    qos_spec_keys = ["%s=%s" % (key, value)
                     for key, value in qos_spec.specs.items()]
    return qos_spec_keys


class QosSpecsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))
    consumer = tables.Column('consumer', verbose_name=_('Consumer'))
    specs = tables.Column(render_spec_keys,
                          verbose_name=_('Specs'),
                          wrap_list=True,
                          filters=(filters.unordered_list,))

    class Meta:
        name = "qos_specs"
        verbose_name = _("QOS Specs")
