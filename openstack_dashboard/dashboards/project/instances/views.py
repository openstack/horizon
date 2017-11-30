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
from collections import OrderedDict
import logging

import futurist

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django import http
from django import shortcuts
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import tables
from horizon import tabs
from horizon.utils import memoized
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.utils import filters

from openstack_dashboard.dashboards.project.instances \
    import console as project_console
from openstack_dashboard.dashboards.project.instances \
    import forms as project_forms
from openstack_dashboard.dashboards.project.instances \
    import tables as project_tables
from openstack_dashboard.dashboards.project.instances \
    import tabs as project_tabs
from openstack_dashboard.dashboards.project.instances \
    import workflows as project_workflows
from openstack_dashboard.views import get_url_with_pagination

LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = project_tables.InstancesTable
    page_title = _("Instances")

    def has_more_data(self, table):
        return self._more

    def get_data(self):
        marker = self.request.GET.get(
            project_tables.InstancesTable._meta.pagination_param, None)
        search_opts = self.get_filters({'marker': marker, 'paginate': True})

        instances = []
        flavors = []
        full_flavors = {}
        images = []
        image_map = {}

        def _task_get_instances():
            # Gather our instances
            try:
                tmp_instances, self._more = api.nova.server_list(
                    self.request,
                    search_opts=search_opts)
                instances.extend(tmp_instances)
            except Exception:
                self._more = False
                exceptions.handle(self.request,
                                  _('Unable to retrieve instances.'))
                # In case of exception when calling nova.server_list
                # don't call api.network
                return

            try:
                api.network.servers_update_addresses(self.request, instances)
            except Exception:
                exceptions.handle(
                    self.request,
                    message=_('Unable to retrieve IP addresses from Neutron.'),
                    ignore=True)

        def _task_get_flavors():
            # Gather our flavors to correlate our instances to them
            try:
                tmp_flavors = api.nova.flavor_list(self.request)
                flavors.extend(tmp_flavors)
                full_flavors.update([(str(flavor.id), flavor)
                                     for flavor in flavors])
            except Exception:
                exceptions.handle(self.request, ignore=True)

        def _task_get_images():
            # Gather our images to correlate our instances to them
            try:
                # TODO(gabriel): Handle pagination.
                tmp_images = api.glance.image_list_detailed(self.request)[0]
                images.extend(tmp_images)
                image_map.update([(str(image.id), image) for image in images])
            except Exception:
                exceptions.handle(self.request, ignore=True)

        with futurist.ThreadPoolExecutor(max_workers=3) as e:
            e.submit(fn=_task_get_flavors)
            e.submit(fn=_task_get_images)

        if 'image_name' in search_opts and \
                not swap_filter(images, search_opts, 'image_name', 'image'):
            self._more = False
            return instances
        elif 'flavor_name' in search_opts and \
                not swap_filter(flavors, search_opts, 'flavor_name', 'flavor'):
            self._more = False
            return instances

        _task_get_instances()

        # Loop through instances to get flavor info.
        for instance in instances:
            if hasattr(instance, 'image'):
                # Instance from image returns dict
                if isinstance(instance.image, dict):
                    if instance.image.get('id') in image_map:
                        instance.image = image_map[instance.image.get('id')]
                    # In case image not found in image_map, set name to empty
                    # to avoid fallback API call to Glance in api/nova.py
                    # until the call is deprecated in api itself
                    else:
                        instance.image['name'] = _("-")

            flavor_id = instance.flavor["id"]
            if flavor_id in full_flavors:
                instance.full_flavor = full_flavors[flavor_id]
            else:
                # If the flavor_id is not in full_flavors list,
                # put info in the log file.
                msg = ('Unable to retrieve flavor "%s" for instance "%s".'
                       % (flavor_id, instance.id))
                LOG.info(msg)

        return instances


def swap_filter(resources, filters, fake_field, real_field):
    if fake_field in filters:
        filter_string = filters[fake_field]
        for resource in resources:
            if resource.name.lower() == filter_string.lower():
                filters[real_field] = resource.id
                del filters[fake_field]
                return True


class LaunchInstanceView(workflows.WorkflowView):
    workflow_class = project_workflows.LaunchInstance

    def get_initial(self):
        initial = super(LaunchInstanceView, self).get_initial()
        initial['project_id'] = self.request.user.tenant_id
        initial['user_id'] = self.request.user.id
        defaults = getattr(settings, 'LAUNCH_INSTANCE_DEFAULTS', {})
        initial['config_drive'] = defaults.get('config_drive', False)
        return initial


def console(request, instance_id):
    data = _('Unable to get log for instance "%s".') % instance_id
    tail = request.GET.get('length')
    if tail and not tail.isdigit():
        msg = _('Log length must be a nonnegative integer.')
        messages.warning(request, msg)
    else:
        try:
            data = api.nova.server_console_output(request,
                                                  instance_id,
                                                  tail_length=tail)
        except Exception:
            exceptions.handle(request, ignore=True)
    return http.HttpResponse(data.encode('utf-8'), content_type='text/plain')


def auto_console(request, instance_id):
    console_type = getattr(settings, 'CONSOLE_TYPE', 'AUTO')
    try:
        instance = api.nova.server_get(request, instance_id)
        console_url = project_console.get_console(request, console_type,
                                                  instance)[1]
        return shortcuts.redirect(console_url)
    except Exception:
        redirect = reverse("horizon:project:instances:index")
        msg = _('Unable to get console for instance "%s".') % instance_id
        exceptions.handle(request, msg, redirect=redirect)


def vnc(request, instance_id):
    try:
        instance = api.nova.server_get(request, instance_id)
        console_url = project_console.get_console(request, 'VNC', instance)[1]
        return shortcuts.redirect(console_url)
    except Exception:
        redirect = reverse("horizon:project:instances:index")
        msg = _('Unable to get VNC console for instance "%s".') % instance_id
        exceptions.handle(request, msg, redirect=redirect)


def spice(request, instance_id):
    try:
        instance = api.nova.server_get(request, instance_id)
        console_url = project_console.get_console(request, 'SPICE',
                                                  instance)[1]
        return shortcuts.redirect(console_url)
    except Exception:
        redirect = reverse("horizon:project:instances:index")
        msg = _('Unable to get SPICE console for instance "%s".') % instance_id
        exceptions.handle(request, msg, redirect=redirect)


def rdp(request, instance_id):
    try:
        instance = api.nova.server_get(request, instance_id)
        console_url = project_console.get_console(request, 'RDP', instance)[1]
        return shortcuts.redirect(console_url)
    except Exception:
        redirect = reverse("horizon:project:instances:index")
        msg = _('Unable to get RDP console for instance "%s".') % instance_id
        exceptions.handle(request, msg, redirect=redirect)


class SerialConsoleView(generic.TemplateView):
    template_name = 'serial_console.html'

    def get_context_data(self, **kwargs):
        context = super(SerialConsoleView, self).get_context_data(**kwargs)
        instance = None
        try:
            instance = api.nova.server_get(self.request,
                                           self.kwargs['instance_id'])
        except Exception:
            context["error_message"] = _(
                "Cannot find instance %s.") % self.kwargs['instance_id']
            # name is unknown, so leave it blank for the window title
            # in full-screen mode, so only the instance id is shown.
            context['page_title'] = self.kwargs['instance_id']
            return context
        context['page_title'] = "%s (%s)" % (instance.name, instance.id)
        try:
            console_url = project_console.get_console(self.request,
                                                      "SERIAL", instance)[1]
            context["console_url"] = console_url
            context["protocols"] = "['binary', 'base64']"
        except exceptions.NotAvailable:
            context["error_message"] = _(
                "Cannot get console for instance %s.") % self.kwargs[
                'instance_id']
        return context


class UpdateView(workflows.WorkflowView):
    workflow_class = project_workflows.UpdateInstance
    success_url = reverse_lazy("horizon:project:instances:index")

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context["instance_id"] = self.kwargs['instance_id']
        return context

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        instance_id = self.kwargs['instance_id']
        try:
            return api.nova.server_get(self.request, instance_id)
        except Exception:
            redirect = reverse("horizon:project:instances:index")
            msg = _('Unable to retrieve instance details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        initial = super(UpdateView, self).get_initial()
        initial.update({'instance_id': self.kwargs['instance_id'],
                        'name': getattr(self.get_object(), 'name', '')})
        return initial


class RebuildView(forms.ModalFormView):
    form_class = project_forms.RebuildInstanceForm
    template_name = 'project/instances/rebuild.html'
    success_url = reverse_lazy('horizon:project:instances:index')
    page_title = _("Rebuild Instance")
    submit_label = page_title

    def get_context_data(self, **kwargs):
        context = super(RebuildView, self).get_context_data(**kwargs)
        context['instance_id'] = self.kwargs['instance_id']
        context['can_set_server_password'] = api.nova.can_set_server_password()
        return context

    def get_initial(self):
        return {'instance_id': self.kwargs['instance_id']}


class DecryptPasswordView(forms.ModalFormView):
    form_class = project_forms.DecryptPasswordInstanceForm
    template_name = 'project/instances/decryptpassword.html'
    success_url = reverse_lazy('horizon:project:instances:index')
    page_title = _("Retrieve Instance Password")

    def get_context_data(self, **kwargs):
        context = super(DecryptPasswordView, self).get_context_data(**kwargs)
        context['instance_id'] = self.kwargs['instance_id']
        context['keypair_name'] = self.kwargs['keypair_name']
        return context

    def get_initial(self):
        return {'instance_id': self.kwargs['instance_id'],
                'keypair_name': self.kwargs['keypair_name']}


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.InstanceDetailTabs
    template_name = 'horizon/common/_detail.html'
    redirect_url = 'horizon:project:instances:index'
    page_title = "{{ instance.name|default:instance.id }}"
    image_url = 'horizon:project:images:images:detail'
    volume_url = 'horizon:project:volumes:detail'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        instance = self.get_data()
        if instance.image:
            instance.image_url = reverse(self.image_url,
                                         args=[instance.image['id']])
        instance.volume_url = self.volume_url
        context["instance"] = instance
        context["url"] = get_url_with_pagination(
            self.request,
            project_tables.InstancesTable._meta.pagination_param,
            project_tables.InstancesTable._meta.prev_pagination_param,
            self.redirect_url)

        context["actions"] = self._get_actions(instance)
        return context

    def _get_actions(self, instance):
        table = project_tables.InstancesTable(self.request)
        return table.render_row_actions(instance)

    @memoized.memoized_method
    def get_data(self):
        instance_id = self.kwargs['instance_id']

        try:
            instance = api.nova.server_get(self.request, instance_id)
        except Exception:
            redirect = reverse(self.redirect_url)
            exceptions.handle(self.request,
                              _('Unable to retrieve details for '
                                'instance "%s".') % instance_id,
                              redirect=redirect)
            # Not all exception types handled above will result in a redirect.
            # Need to raise here just in case.
            raise exceptions.Http302(redirect)

        choices = project_tables.STATUS_DISPLAY_CHOICES
        instance.status_label = (
            filters.get_display_label(choices, instance.status))

        def _task_get_volumes():
            try:
                instance.volumes = api.nova.instance_volumes_list(self.request,
                                                                  instance_id)
                # Sort by device name
                instance.volumes.sort(key=lambda vol: vol.device)
            except Exception:
                msg = _('Unable to retrieve volume list for instance '
                        '"%(name)s" (%(id)s).') % {'name': instance.name,
                                                   'id': instance_id}
                exceptions.handle(self.request, msg, ignore=True)

        def _task_get_flavor():
            try:
                instance.full_flavor = api.nova.flavor_get(
                    self.request, instance.flavor["id"])
            except Exception:
                msg = _('Unable to retrieve flavor information for instance '
                        '"%(name)s" (%(id)s).') % {'name': instance.name,
                                                   'id': instance_id}
                exceptions.handle(self.request, msg, ignore=True)

        def _task_get_security_groups():
            try:
                instance.security_groups = api.neutron.server_security_groups(
                    self.request, instance_id)
            except Exception:
                msg = _('Unable to retrieve security groups for instance '
                        '"%(name)s" (%(id)s).') % {'name': instance.name,
                                                   'id': instance_id}
                exceptions.handle(self.request, msg, ignore=True)

        def _task_update_addresses():
            try:
                api.network.servers_update_addresses(self.request, [instance])
            except Exception:
                msg = _('Unable to retrieve IP addresses from Neutron for '
                        'instance "%(name)s" (%(id)s).') \
                    % {'name': instance.name, 'id': instance_id}
                exceptions.handle(self.request, msg, ignore=True)

        with futurist.ThreadPoolExecutor(max_workers=4) as e:
            e.submit(fn=_task_get_volumes)
            e.submit(fn=_task_get_flavor)
            e.submit(fn=_task_get_security_groups)
            e.submit(fn=_task_update_addresses)

        return instance

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

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        instance_id = self.kwargs['instance_id']
        try:
            instance = api.nova.server_get(self.request, instance_id)
        except Exception:
            redirect = reverse("horizon:project:instances:index")
            msg = _('Unable to retrieve instance details.')
            exceptions.handle(self.request, msg, redirect=redirect)
        flavor_id = instance.flavor['id']
        flavors = self.get_flavors()
        if flavor_id in flavors:
            instance.flavor_name = flavors[flavor_id].name
        else:
            try:
                flavor = api.nova.flavor_get(self.request, flavor_id)
                instance.flavor_name = flavor.name
            except Exception:
                msg = _('Unable to retrieve flavor information for instance '
                        '"%s".') % instance_id
                exceptions.handle(self.request, msg, ignore=True)
                instance.flavor_name = _("Not available")
        return instance

    @memoized.memoized_method
    def get_flavors(self, *args, **kwargs):
        try:
            flavors = api.nova.flavor_list(self.request)
            return OrderedDict((str(flavor.id), flavor) for flavor in flavors)
        except Exception:
            redirect = reverse("horizon:project:instances:index")
            exceptions.handle(self.request,
                              _('Unable to retrieve flavors.'),
                              redirect=redirect)

    def get_initial(self):
        initial = super(ResizeView, self).get_initial()
        _object = self.get_object()
        if _object:
            initial.update(
                {'instance_id': self.kwargs['instance_id'],
                 'name': getattr(_object, 'name', None),
                 'old_flavor_id': _object.flavor['id'],
                 'old_flavor_name': getattr(_object, 'flavor_name', ''),
                 'flavors': self.get_flavors()})
        return initial


class AttachInterfaceView(forms.ModalFormView):
    form_class = project_forms.AttachInterface
    template_name = 'project/instances/attach_interface.html'
    page_title = _("Attach Interface")
    form_id = "attach_interface_form"
    submit_label = _("Attach Interface")
    success_url = reverse_lazy('horizon:project:instances:index')

    def get_context_data(self, **kwargs):
        context = super(AttachInterfaceView, self).get_context_data(**kwargs)
        context['instance_id'] = self.kwargs['instance_id']
        return context

    def get_initial(self):
        args = {'instance_id': self.kwargs['instance_id']}
        submit_url = "horizon:project:instances:attach_interface"
        self.submit_url = reverse(submit_url, kwargs=args)
        return args


class AttachVolumeView(forms.ModalFormView):
    form_class = project_forms.AttachVolume
    template_name = 'project/instances/attach_volume.html'
    page_title = _("Attach Volume")
    modal_id = "attach_volume_modal"
    submit_label = _("Attach Volume")
    success_url = reverse_lazy('horizon:project:instances:index')

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.nova.server_get(self.request,
                                       self.kwargs["instance_id"])
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve instance."))

    def get_initial(self):
        args = {'instance_id': self.kwargs['instance_id']}
        submit_url = "horizon:project:instances:attach_volume"
        self.submit_url = reverse(submit_url, kwargs=args)
        try:
            volume_list = api.cinder.volume_list(self.request)
        except Exception:
            volume_list = []
            exceptions.handle(self.request,
                              _("Unable to retrieve volume information."))
        return {"instance_id": self.kwargs["instance_id"],
                "volume_list": volume_list}

    def get_context_data(self, **kwargs):
        context = super(AttachVolumeView, self).get_context_data(**kwargs)
        context['instance_id'] = self.kwargs['instance_id']
        return context


class DetachVolumeView(forms.ModalFormView):
    form_class = project_forms.DetachVolume
    template_name = 'project/instances/detach_volume.html'
    page_title = _("Detach Volume")
    modal_id = "detach_volume_modal"
    submit_label = _("Detach Volume")
    success_url = reverse_lazy('horizon:project:instances:index')

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.nova.server_get(self.request,
                                       self.kwargs['instance_id'])
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve instance."))

    def get_initial(self):
        args = {'instance_id': self.kwargs['instance_id']}
        submit_url = "horizon:project:instances:detach_volume"
        self.submit_url = reverse(submit_url, kwargs=args)
        return {"instance_id": self.kwargs["instance_id"]}

    def get_context_data(self, **kwargs):
        context = super(DetachVolumeView, self).get_context_data(**kwargs)
        context['instance_id'] = self.kwargs['instance_id']
        return context


class DetachInterfaceView(forms.ModalFormView):
    form_class = project_forms.DetachInterface
    template_name = 'project/instances/detach_interface.html'
    page_title = _("Detach Interface")
    form_id = "detach_interface_form"
    submit_label = _("Detach Interface")
    success_url = reverse_lazy('horizon:project:instances:index')

    def get_context_data(self, **kwargs):
        context = super(DetachInterfaceView, self).get_context_data(**kwargs)
        context['instance_id'] = self.kwargs['instance_id']
        return context

    def get_initial(self):
        args = {"instance_id": self.kwargs["instance_id"]}
        submit_url = "horizon:project:instances:detach_interface"
        self.submit_url = reverse(submit_url, kwargs=args)
        return args
