# Copyright 2019 vmware, Inc.
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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = "admin/rbac_policies/_detail_overview.html"
    preload = False

    @memoized.memoized_method
    def _get_data(self):
        rbac_policy = {}
        rbac_policy_id = None
        try:
            rbac_policy_id = self.tab_group.kwargs['rbac_policy_id']
            rbac_policy = api.neutron.rbac_policy_get(self.request,
                                                      rbac_policy_id)

        except Exception:
            msg = _('Unable to retrieve details for rbac_policy "%s".') \
                % (rbac_policy_id)
            exceptions.handle(self.request, msg)
        return rbac_policy

    def get_context_data(self, request, **kwargs):
        context = super(OverviewTab, self).get_context_data(request, **kwargs)
        rbac_policy = self._get_data()

        context["rbac_policy"] = rbac_policy
        return context


class RBACDetailsTabs(tabs.DetailTabsGroup):
    slug = "rbac_policy_tabs"
    tabs = (OverviewTab, )
    sticky = True
