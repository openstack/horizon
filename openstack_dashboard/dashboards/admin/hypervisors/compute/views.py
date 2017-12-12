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

from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.hypervisors.compute \
    import forms as project_forms


class EvacuateHostView(forms.ModalFormView):
    form_class = project_forms.EvacuateHostForm
    template_name = 'admin/hypervisors/compute/evacuate_host.html'
    context_object_name = 'compute_host'
    success_url = reverse_lazy("horizon:admin:hypervisors:index")
    page_title = _("Evacuate Host")
    submit_label = page_title

    def get_context_data(self, **kwargs):
        context = super(EvacuateHostView, self).get_context_data(**kwargs)
        context["compute_host"] = self.kwargs['compute_host']
        return context

    def get_active_compute_hosts_names(self, *args, **kwargs):
        try:
            services = api.nova.service_list(self.request,
                                             binary='nova-compute')
            return [service.host for service in services
                    if service.state == 'up']
        except Exception:
            redirect = reverse("horizon:admin:hypervisors:index")
            msg = _('Unable to retrieve compute host information.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        initial = super(EvacuateHostView, self).get_initial()
        hosts = self.get_active_compute_hosts_names()
        current_host = self.kwargs['compute_host']
        initial.update({'current_host': current_host,
                        'hosts': hosts})
        return initial


class DisableServiceView(forms.ModalFormView):
    form_class = project_forms.DisableServiceForm
    template_name = 'admin/hypervisors/compute/disable_service.html'
    context_object_name = 'compute_host'
    success_url = reverse_lazy("horizon:admin:hypervisors:index")
    page_title = _("Disable Service")
    submit_label = page_title

    def get_context_data(self, **kwargs):
        context = super(DisableServiceView, self).get_context_data(**kwargs)
        context["compute_host"] = self.kwargs['compute_host']
        return context

    def get_initial(self):
        initial = super(DisableServiceView, self).get_initial()
        initial.update({'host': self.kwargs['compute_host']})
        return initial


class MigrateHostView(forms.ModalFormView):
    form_class = project_forms.MigrateHostForm
    template_name = 'admin/hypervisors/compute/migrate_host.html'
    context_object_name = 'compute_host'
    success_url = reverse_lazy("horizon:admin:hypervisors:index")
    page_title = _("Migrate Host")
    submit_label = page_title

    def get_context_data(self, **kwargs):
        context = super(MigrateHostView, self).get_context_data(**kwargs)
        context["compute_host"] = self.kwargs['compute_host']
        return context

    def get_initial(self):
        initial = super(MigrateHostView, self).get_initial()
        current_host = self.kwargs['compute_host']

        initial.update({
            'current_host': current_host,
            'live_migrate': True,
            'block_migration': False,
            'disk_over_commit': False
        })
        return initial
