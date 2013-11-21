# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
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


from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import tabs
from openstack_dashboard import api
from openstack_dashboard.api import ceilometer


class GlobalStatsTab(tabs.Tab):
    name = _("Stats")
    slug = "stats"
    template_name = ("admin/metering/stats.html")
    preload = False

    @staticmethod
    def _get_flavor_names(request):
        try:
            flavors = api.nova.flavor_list(request, None)
            return [f.name for f in flavors]
        except Exception:
            return ['m1.tiny', 'm1.small', 'm1.medium',
                    'm1.large', 'm1.xlarge']

    def get_context_data(self, request):
        query = [{"field": "metadata.OS-EXT-AZ:availability_zone",
                  "op": "eq",
                  "value": "nova"}]
        try:
            instances = ceilometer.resource_list(request, query,
                ceilometer_usage_object=None)
            meters = ceilometer.meter_list(request)
        except Exception:
            instances = []
            meters = []
            exceptions.handle(request,
                              _('Unable to retrieve Nova Ceilometer '
                                'metering information.'))
        instance_ids = set([i.resource_id for i in instances])
        instance_meters = set([m.name for m in meters
                               if m.resource_id in instance_ids])

        meter_titles = {"instance": _("Duration of instance"),
                        "memory": _("Volume of RAM in MB"),
                        "cpu": _("CPU time used"),
                        "cpu_util": _("Average CPU utilisation"),
                        "vcpus": _("Number of VCPUs"),
                        "disk.read.requests": _("Number of read requests"),
                        "disk.write.requests": _("Number of write requests"),
                        "disk.read.bytes": _("Volume of reads in B"),
                        "disk.write.bytes": _("Volume of writes in B"),
                        "disk.root.size": _("Size of root disk in GB"),
                        "disk.ephemeral.size": _("Size of ephemeral disk "
                            "in GB"),
                        "network.incoming.bytes": _("Number of incoming bytes "
                            "on the network for a VM interface"),
                        "network.outgoing.bytes": _("Number of outgoing bytes "
                            "on the network for a VM interface"),
                        "network.incoming.packets": _("Number of incoming "
                            "packets for a VM interface"),
                        "network.outgoing.packets": _("Number of outgoing "
                            "packets for a VM interface")}

        for flavor in self._get_flavor_names(request):
            name = 'instance:%s' % flavor
            hint = (_('Duration of instance type %s (openstack flavor)') %
                    flavor)
            meter_titles[name] = hint

        class MetersWrap(object):
            """ A quick wrapper for meter and associated titles. """
            def __init__(self, meter, meter_titles):
                self.name = meter
                self.title = meter_titles.get(meter, "")

        meters_objs = [MetersWrap(meter, meter_titles)
                       for meter in sorted(instance_meters)]

        context = {'meters': meters_objs}
        return context


class CeilometerOverviewTabs(tabs.TabGroup):
    slug = "ceilometer_overview"
    tabs = (GlobalStatsTab,)
    sticky = True
