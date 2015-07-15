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

import logging

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils import datastructures
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api

from openstack_dashboard.dashboards.router.nexus1000v \
    import forms as profileforms
from openstack_dashboard.dashboards.router.nexus1000v \
    import tables as profiletables


LOG = logging.getLogger(__name__)


def _get_tenant_list(request):
    tenants = []
    try:
        tenants, has_more = api.keystone.tenant_list(request)
    except Exception:
        msg = _('Unable to retrieve project information.')
        exceptions.handle(request, msg)

    return datastructures.SortedDict([(t.id, t) for t in tenants])


def _get_profiles(request, type_p):
    try:
        profiles = api.neutron.profile_list(request, type_p)
    except Exception:
        profiles = []
        msg = _('Network Profiles could not be retrieved.')
        exceptions.handle(request, msg)
    return profiles


class NetworkProfileIndexView(tables.DataTableView):
    table_class = profiletables.NetworkProfile
    template_name = 'router/nexus1000v/network_profile/index.html'
    page_title = _("Cisco Nexus 1000V")

    def get_data(self):
        return _get_profiles(self.request, 'network')


class PolicyProfileIndexView(tables.DataTableView):
    table_class = profiletables.PolicyProfile
    template_name = 'router/nexus1000v/policy_profile/index.html'
    page_title = _("Cisco Nexus 1000V")

    def get_data(self):
        return _get_profiles(self.request, 'policy')


class IndexTabGroup(tabs.TabGroup):
    slug = "group"
    tabs = (NetworkProfileIndexView, PolicyProfileIndexView,)


class IndexView(tables.MultiTableView):
    table_classes = (profiletables.PolicyProfile,)
    template_name = 'router/nexus1000v/index.html'
    page_title = _("Cisco Nexus 1000V")

    def get_network_profile_data(self):
        return _get_profiles(self.request, 'network')

    def get_policy_profile_data(self):
        return _get_profiles(self.request, 'policy')


class CreateNetworkProfileView(forms.ModalFormView):
    form_class = profileforms.CreateNetworkProfile
    form_id = "create_network_profile_form"
    modal_header = _("Create Network Profile")
    template_name = 'router/nexus1000v/create_network_profile.html'
    submit_label = _("Create Network Profile")
    submit_url = reverse_lazy(
        "horizon:router:nexus1000v:create_network_profile")
    success_url = reverse_lazy('horizon:router:nexus1000v:index')
    page_title = _("Create Network Profile")


class UpdateNetworkProfileView(forms.ModalFormView):
    form_class = profileforms.UpdateNetworkProfile
    form_id = "update_network_profile_form"
    modal_header = _("Edit Network Profile")
    template_name = 'router/nexus1000v/update_network_profile.html'
    context_object_name = 'network_profile'
    submit_label = _("Save Changes")
    submit_url = "horizon:router:nexus1000v:update_network_profile"
    success_url = reverse_lazy('horizon:router:nexus1000v:index')
    page_title = _("Update Network Profile")

    def get_context_data(self, **kwargs):
        context = super(UpdateNetworkProfileView,
                        self).get_context_data(**kwargs)
        context["profile_id"] = self.kwargs['profile_id']
        args = (self.kwargs['profile_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        profile_id = self.kwargs['profile_id']
        try:
            profile = api.neutron.profile_get(self.request,
                                              profile_id)
            LOG.debug("Network Profile object=%s", profile)
            return profile
        except Exception:
            redirect = self.success_url
            msg = _('Unable to retrieve network profile details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        profile = self._get_object()
        # Set project name
        tenant_dict = _get_tenant_list(self.request)
        try:
            bindings = api.neutron.profile_bindings_list(
                self.request, 'network')
        except Exception:
            msg = _('Failed to obtain network profile binding')
            redirect = self.success_url
            exceptions.handle(self.request, msg, redirect=redirect)
        bindings_dict = datastructures.SortedDict(
            [(b.profile_id, b.tenant_id) for b in bindings])
        project_id = bindings_dict.get(profile.id)
        project = tenant_dict.get(project_id)
        project_name = getattr(project, 'name', project_id)
        return {'profile_id': profile['id'],
                'name': profile['name'],
                'segment_range': profile['segment_range'],
                'segment_type': profile['segment_type'],
                'physical_network': profile['physical_network'],
                'sub_type': profile['sub_type'],
                'multicast_ip_range': profile['multicast_ip_range'],
                'project': project_name}
