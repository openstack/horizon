# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.template import defaultfilters as filters
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables
from horizon.utils import filters as utils_filters

from openstack_dashboard import api


class EvacuateHost(tables.LinkAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Evacuate Host",
            u"Evacuate Hosts",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Evacuated Host",
            u"Evacuated Hosts",
            count
        )

    name = "evacuate"
    verbose_name = _("Evacuate Host")
    url = "horizon:admin:hypervisors:compute:evacuate_host"
    classes = ("ajax-modal", "btn-migrate")
    policy_rules = (("compute", "compute_extension:evacuate"),)

    def __init__(self, **kwargs):
        super(EvacuateHost, self).__init__(**kwargs)
        self.name = kwargs.get('name', self.name)

    def allowed(self, request, instance):
        if not api.nova.extension_supported('AdminActions', request):
            return False

        return self.datum.state == "down"


class ComputeHostFilterAction(tables.FilterAction):
    def filter(self, table, services, filter_string):
        q = filter_string.lower()

        return filter(lambda service: q in service.type.lower(), services)


class ComputeHostTable(tables.DataTable):
    host = tables.Column('host', verbose_name=_('Host'))
    zone = tables.Column('zone', verbose_name=_('Zone'))
    status = tables.Column('status', verbose_name=_('Status'))
    state = tables.Column('state', verbose_name=_('State'))
    updated_at = tables.Column('updated_at',
                               verbose_name=_('Updated At'),
                               filters=(utils_filters.parse_isotime,
                                        filters.timesince))

    def get_object_id(self, obj):
        return obj.host

    class Meta:
        name = "compute_host"
        verbose_name = _("Compute Host")
        table_actions = (ComputeHostFilterAction,)
        multi_select = False
        row_actions = (EvacuateHost,)
