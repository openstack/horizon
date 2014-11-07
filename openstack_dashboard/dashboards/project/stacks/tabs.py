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

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import messages
from horizon import tabs
from openstack_dashboard import api
from openstack_dashboard import policy

from openstack_dashboard.dashboards.project.stacks \
    import api as project_api
from openstack_dashboard.dashboards.project.stacks import mappings
from openstack_dashboard.dashboards.project.stacks \
    import tables as project_tables


LOG = logging.getLogger(__name__)


class StackTopologyTab(tabs.Tab):
    name = _("Topology")
    slug = "topology"
    template_name = "project/stacks/_detail_topology.html"
    preload = False

    def allowed(self, request):
        return policy.check(
            (("orchestration", "cloudformation:DescribeStacks"),
             ("orchestration", "cloudformation:ListStackResources"),),
            request)

    def get_context_data(self, request):
        context = {}
        stack = self.tab_group.kwargs['stack']
        context['stack_id'] = stack.id
        context['d3_data'] = project_api.d3_data(request, stack_id=stack.id)
        return context


class StackOverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = "project/stacks/_detail_overview.html"

    def allowed(self, request):
        return policy.check(
            (("orchestration", "cloudformation:DescribeStacks"),),
            request)

    def get_context_data(self, request):
        return {"stack": self.tab_group.kwargs['stack']}


class ResourceOverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "resource_overview"
    template_name = "project/stacks/_resource_overview.html"

    def allowed(self, request):
        return policy.check(
            (("orchestration", "cloudformation:DescribeStackResource"),),
            request)

    def get_context_data(self, request):
        resource = self.tab_group.kwargs['resource']
        resource_url = mappings.resource_to_url(resource)
        return {
            "resource": resource,
            "resource_url": resource_url,
            "metadata": self.tab_group.kwargs['metadata']}


class StackEventsTab(tabs.Tab):
    name = _("Events")
    slug = "events"
    template_name = "project/stacks/_detail_events.html"
    preload = False

    def allowed(self, request):
        return policy.check(
            (("orchestration", "cloudformation:DescribeStackEvents"),),
            request)

    def get_context_data(self, request):
        stack = self.tab_group.kwargs['stack']
        try:
            stack_identifier = '%s/%s' % (stack.stack_name, stack.id)
            events = api.heat.events_list(self.request, stack_identifier)
            LOG.debug('got events %s' % events)
            # The stack id is needed to generate the resource URL.
            for event in events:
                event.stack_id = stack.id
        except Exception:
            events = []
            messages.error(request, _(
                'Unable to get events for stack "%s".') % stack.stack_name)
        return {"stack": stack,
                "table": project_tables.EventsTable(request, data=events), }


class StackResourcesTab(tabs.Tab):
    name = _("Resources")
    slug = "resources"
    template_name = "project/stacks/_detail_resources.html"
    preload = False

    def allowed(self, request):
        return policy.check(
            (("orchestration", "cloudformation:ListStackResources"),),
            request)

    def get_context_data(self, request):
        stack = self.tab_group.kwargs['stack']
        try:
            stack_identifier = '%s/%s' % (stack.stack_name, stack.id)
            resources = api.heat.resources_list(self.request, stack_identifier)
            LOG.debug('got resources %s' % resources)
            # The stack id is needed to generate the resource URL.
            for r in resources:
                r.stack_id = stack.id
        except Exception:
            resources = []
            messages.error(request, _(
                'Unable to get resources for stack "%s".') % stack.stack_name)
        return {"stack": stack,
                "table": project_tables.ResourcesTable(
                    request, data=resources, stack=stack), }


class StackTemplateTab(tabs.Tab):
    name = _("Template")
    slug = "stack_template"
    template_name = "project/stacks/_stack_template.html"

    def allowed(self, request):
        return policy.check(
            (("orchestration", "cloudformation:DescribeStacks"),),
            request)

    def get_context_data(self, request):
        return {"stack_template": self.tab_group.kwargs['stack_template']}


class StackDetailTabs(tabs.TabGroup):
    slug = "stack_details"
    tabs = (StackTopologyTab, StackOverviewTab, StackResourcesTab,
            StackEventsTab, StackTemplateTab)
    sticky = True


class ResourceDetailTabs(tabs.TabGroup):
    slug = "resource_details"
    tabs = (ResourceOverviewTab,)
    sticky = True
