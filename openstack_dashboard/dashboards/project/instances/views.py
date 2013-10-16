# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

"""
Views for managing instances.
"""
from django.core.urlresolvers import reverse  # noqa
from django.core.urlresolvers import reverse_lazy  # noqa
from django import http
from django import shortcuts
from django.utils.datastructures import SortedDict  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.instances \
    import forms as project_forms
from openstack_dashboard.dashboards.project.instances \
    import tables as project_tables
from openstack_dashboard.dashboards.project.instances \
    import tabs as project_tabs
from openstack_dashboard.dashboards.project.instances \
    import workflows as project_workflows


class IndexView(tables.DataTableView):
    table_class = project_tables.InstancesTable
    template_name = 'project/instances/index.html'

    def has_more_data(self, table):
        return self._more

    def get_data(self):
        marker = self.request.GET.get(
            project_tables.InstancesTable._meta.pagination_param, None)
        # Gather our instances
        try:
            instances, self._more = api.nova.server_list(
                self.request,
                search_opts={'marker': marker,
                             'paginate': True})
        except Exception:
            self._more = False
            instances = []
            exceptions.handle(self.request,
                              _('Unable to retrieve instances.'))
        # Gather our flavors and images and correlate our instances to them
        if instances:
            try:
                flavors = api.nova.flavor_list(self.request)
            except Exception:
                flavors = []
                exceptions.handle(self.request, ignore=True)

            try:
                # TODO(gabriel): Handle pagination.
                images, more = api.glance.image_list_detailed(self.request)
            except Exception:
                images = []
                exceptions.handle(self.request, ignore=True)

            full_flavors = SortedDict([(str(flavor.id), flavor)
                                       for flavor in flavors])
            image_map = SortedDict([(str(image.id), image)
                                    for image in images])

            # Loop through instances to get flavor info.
            for instance in instances:
                if hasattr(instance, 'image'):
                    # Instance from image returns dict
                    if isinstance(instance.image, dict):
                        if instance.image.get('id') in image_map:
                            instance.image = image_map[instance.image['id']]
                    else:
                        # Instance from volume returns a string
                        instance.image = {'name':
                                instance.image if instance.image else _("-")}

                try:
                    flavor_id = instance.flavor["id"]
                    if flavor_id in full_flavors:
                        instance.full_flavor = full_flavors[flavor_id]
                    else:
                        # If the flavor_id is not in full_flavors list,
                        # get it via nova api.
                        instance.full_flavor = api.nova.flavor_get(
                            self.request, flavor_id)
                except Exception:
                    msg = _('Unable to retrieve instance size information.')
                    exceptions.handle(self.request, msg)
        return instances


class LaunchInstanceView(workflows.WorkflowView):
    workflow_class = project_workflows.LaunchInstance

    def get_initial(self):
        initial = super(LaunchInstanceView, self).get_initial()
        initial['project_id'] = self.request.user.tenant_id
        initial['user_id'] = self.request.user.id
        return initial


def console(request, instance_id):
    try:
        # TODO(jakedahn): clean this up once the api supports tailing.
        tail = request.GET.get('length', None)
        data = api.nova.server_console_output(request,
                                              instance_id,
                                              tail_length=tail)
    except Exception:
        data = _('Unable to get log for instance "%s".') % instance_id
        exceptions.handle(request, ignore=True)
    response = http.HttpResponse(mimetype='text/plain')
    response.write(data)
    response.flush()
    return response


def vnc(request, instance_id):
    try:
        console = api.nova.server_vnc_console(request, instance_id)
        instance = api.nova.server_get(request, instance_id)
        return shortcuts.redirect(console.url +
                ("&title=%s(%s)" % (instance.name, instance_id)))
    except Exception:
        redirect = reverse("horizon:project:instances:index")
        msg = _('Unable to get VNC console for instance "%s".') % instance_id
        exceptions.handle(request, msg, redirect=redirect)


def spice(request, instance_id):
    try:
        console = api.nova.server_spice_console(request, instance_id)
        instance = api.nova.server_get(request, instance_id)
        return shortcuts.redirect(console.url +
                ("&title=%s(%s)" % (instance.name, instance_id)))
    except Exception:
        redirect = reverse("horizon:project:instances:index")
        msg = _('Unable to get SPICE console for instance "%s".') % instance_id
        exceptions.handle(request, msg, redirect=redirect)


class UpdateView(workflows.WorkflowView):
    workflow_class = project_workflows.UpdateInstance
    success_url = reverse_lazy("horizon:project:instances:index")

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context["instance_id"] = self.kwargs['instance_id']
        return context

    def get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            instance_id = self.kwargs['instance_id']
            try:
                self._object = api.nova.server_get(self.request, instance_id)
            except Exception:
                redirect = reverse("horizon:project:instances:index")
                msg = _('Unable to retrieve instance details.')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_initial(self):
        initial = super(UpdateView, self).get_initial()
        initial.update({'instance_id': self.kwargs['instance_id'],
                'name': getattr(self.get_object(), 'name', '')})
        return initial


class RebuildView(forms.ModalFormView):
    form_class = project_forms.RebuildInstanceForm
    template_name = 'project/instances/rebuild.html'
    success_url = reverse_lazy('horizon:project:instances:index')

    def get_context_data(self, **kwargs):
        context = super(RebuildView, self).get_context_data(**kwargs)
        context['instance_id'] = self.kwargs['instance_id']
        return context

    def get_initial(self):
        return {'instance_id': self.kwargs['instance_id']}


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.InstanceDetailTabs
    template_name = 'project/instances/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["instance"] = self.get_data()
        return context

    def get_data(self):
        if not hasattr(self, "_instance"):
            try:
                instance_id = self.kwargs['instance_id']
                instance = api.nova.server_get(self.request, instance_id)
                instance.volumes = api.nova.instance_volumes_list(self.request,
                                                                  instance_id)
                # Sort by device name
                instance.volumes.sort(key=lambda vol: vol.device)
                instance.full_flavor = api.nova.flavor_get(
                    self.request, instance.flavor["id"])
                instance.security_groups = api.network.server_security_groups(
                    self.request, instance_id)
            except Exception:
                redirect = reverse('horizon:project:instances:index')
                exceptions.handle(self.request,
                                  _('Unable to retrieve details for '
                                    'instance "%s".') % instance_id,
                                    redirect=redirect)
            self._instance = instance
        return self._instance

    def get_tabs(self, request, *args, **kwargs):
        instance = self.get_data()
        return self.tab_group_class(request, instance=instance, **kwargs)


class ResizeView(workflows.WorkflowView):
    workflow_class = project_workflows.ResizeInstance
    success_url = reverse_lazy("horizon:project:instances:index")

    def get_context_data(self, **kwargs):
        context = super(ResizeView, self).get_context_data(**kwargs)
        context["instance_id"] = self.kwargs['instance_id']
        return context

    def get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            instance_id = self.kwargs['instance_id']
            try:
                self._object = api.nova.server_get(self.request, instance_id)
                flavor_id = self._object.flavor['id']
                flavors = self.get_flavors()
                if flavor_id in flavors:
                    self._object.flavor_name = flavors[flavor_id].name
                else:
                    flavor = api.nova.flavor_get(self.request, flavor_id)
                    self._object.flavor_name = flavor.name
            except Exception:
                redirect = reverse("horizon:project:instances:index")
                msg = _('Unable to retrieve instance details.')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_flavors(self, *args, **kwargs):
        if not hasattr(self, "_flavors"):
            try:
                flavors = api.nova.flavor_list(self.request)
                self._flavors = SortedDict([(str(flavor.id), flavor)
                                        for flavor in flavors])
            except Exception:
                redirect = reverse("horizon:project:instances:index")
                exceptions.handle(self.request,
                    _('Unable to retrieve flavors.'), redirect=redirect)
        return self._flavors

    def get_initial(self):
        initial = super(ResizeView, self).get_initial()
        _object = self.get_object()
        if _object:
            initial.update({'instance_id': self.kwargs['instance_id'],
                'name': getattr(_object, 'name', None),
                'old_flavor_id': _object.flavor['id'],
                'old_flavor_name': getattr(_object, 'flavor_name', ''),
                'flavors': self.get_flavors()})
        return initial
