#    (c) Copyright 2014 Hewlett-Packard Development Company, L.P.
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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard.api import glance
from openstack_dashboard.dashboards.admin.metadata_defs \
    import constants


class OverviewTab(tabs.Tab):
    name = _("Namespace Overview")
    slug = "overview"
    template_name = constants.METADATA_DETAIL_OVERVIEW_TEMPLATE

    def get_context_data(self, request):
        namespace_name = self.tab_group.kwargs['namespace_id']
        try:
            namespace = glance.metadefs_namespace_get(request,
                                                      namespace_name,
                                                      wrap=True)
        except Exception:
            namespace = None
            msg = _('Unable to retrieve namespace details.')
            exceptions.handle(request, msg)

        return {"namespace": namespace}


class ContentsTab(tabs.Tab):
    name = _("Contents")
    slug = "contents"
    template_name = constants.METADATA_DETAIL_CONTENTS_TEMPLATE
    preload = False

    def get_context_data(self, request):
        namespace_id = self.tab_group.kwargs['namespace_id']
        try:
            namespace = glance.metadefs_namespace_get(request,
                                                      namespace_id,
                                                      wrap=True)
        except Exception:
            msg = _('Unable to retrieve namespace contents.')
            exceptions.handle(request, msg)
            return None

        return {
            'namespace_name': namespace.namespace,
            "namespace_contents": namespace.as_json()}


class NamespaceDetailTabs(tabs.TabGroup):
    slug = "namespace_details"
    tabs = (OverviewTab, ContentsTab)
