# Copyright (c) 2014 eBay Software Foundation
# Copyright 2015 HP Software, LLC
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django import template
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from openstack_dashboard.contrib.trove import api
from openstack_dashboard.contrib.trove.content.database_clusters import tables


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"

    def get_context_data(self, request):
        return {"cluster": self.tab_group.kwargs['cluster']}

    def get_template_name(self, request):
        cluster = self.tab_group.kwargs['cluster']
        template_file = ('project/database_clusters/_detail_overview_%s.html'
                         % cluster.datastore['type'])
        try:
            template.loader.get_template(template_file)
            return template_file
        except template.TemplateDoesNotExist:
            # This datastore type does not have a template file
            # Just use the base template file
            return ('project/database_clusters/_detail_overview.html')


class InstancesTab(tabs.TableTab):
    table_classes = (tables.InstancesTable,)
    name = _("Instances")
    slug = "instances_tab"
    cluster = None
    template_name = "horizon/common/_detail_table.html"
    preload = True

    def get_instances_data(self):
        cluster = self.tab_group.kwargs['cluster']
        data = []
        try:
            instances = api.trove.cluster_get(self.request,
                                              cluster.id).instances
            for instance in instances:
                instance_info = api.trove.instance_get(self.request,
                                                       instance['id'])
                flavor_id = instance_info.flavor['id']
                instance_info.full_flavor = api.trove.flavor_get(self.request,
                                                                 flavor_id)
                if "type" in instance:
                    instance_info.type = instance["type"]
                if "ip" in instance:
                    instance_info.ip = instance["ip"]
                if "hostname" in instance:
                    instance_info.hostname = instance["hostname"]

                data.append(instance_info)
        except Exception:
            msg = _('Unable to get instances data.')
            exceptions.handle(self.request, msg)
            data = []
        return data


class ClusterDetailTabs(tabs.TabGroup):
    slug = "cluster_details"
    tabs = (OverviewTab, InstancesTab)
    sticky = True
