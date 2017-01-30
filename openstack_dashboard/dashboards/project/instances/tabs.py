# Copyright 2012 Nebula, Inc.
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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from horizon.utils import functions as utils

from openstack_dashboard.dashboards.project.instances \
    import audit_tables as a_tables

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.instances import console


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = ("project/instances/"
                     "_detail_overview.html")

    def get_context_data(self, request):
        return {"instance": self.tab_group.kwargs['instance'],
                "is_superuser": request.user.is_superuser}


class LogTab(tabs.Tab):
    name = _("Log")
    slug = "log"
    template_name = "project/instances/_detail_log.html"
    preload = False

    def get_context_data(self, request):
        instance = self.tab_group.kwargs['instance']
        log_length = utils.get_log_length(request)
        try:
            data = api.nova.server_console_output(request,
                                                  instance.id,
                                                  tail_length=log_length)
        except Exception:
            data = _('Unable to get log for instance "%s".') % instance.id
            exceptions.handle(request, ignore=True)
        return {"instance": instance,
                "console_log": data,
                "log_length": log_length}


class ConsoleTab(tabs.Tab):
    name = _("Console")
    slug = "console"
    template_name = "project/instances/_detail_console.html"
    preload = False

    def get_context_data(self, request):
        instance = self.tab_group.kwargs['instance']
        console_type = getattr(settings, 'CONSOLE_TYPE', 'AUTO')
        console_url = None
        try:
            console_type, console_url = console.get_console(
                request, console_type, instance)
            # For serial console, the url is different from VNC, etc.
            # because it does not include params for title and token
            if console_type == "SERIAL":
                console_url = reverse('horizon:project:instances:serial',
                                      args=[instance.id])
        except exceptions.NotAvailable:
            exceptions.handle(request, ignore=True, force_log=True)

        return {'console_url': console_url, 'instance_id': instance.id,
                'console_type': console_type}

    def allowed(self, request):
        # The ConsoleTab is available if settings.CONSOLE_TYPE is not set at
        # all, or if it's set to any value other than None or False.
        return bool(getattr(settings, 'CONSOLE_TYPE', True))


class AuditTab(tabs.TableTab):
    name = _("Action Log")
    slug = "audit"
    table_classes = (a_tables.AuditTable,)
    template_name = "project/instances/_detail_audit.html"
    preload = False

    def get_audit_data(self):
        actions = []
        try:
            actions = api.nova.instance_action_list(
                self.request, self.tab_group.kwargs['instance_id'])
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve instance action list.'))

        return sorted(actions, reverse=True, key=lambda y: y.start_time)


class InstanceDetailTabs(tabs.DetailTabsGroup):
    slug = "instance_details"
    tabs = (OverviewTab, LogTab, ConsoleTab, AuditTab)
    sticky = True
