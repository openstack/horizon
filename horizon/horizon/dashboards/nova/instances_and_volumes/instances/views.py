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
Views for managing Nova instances.
"""
import logging

from django import http
from django import shortcuts
from django.core.urlresolvers import reverse
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext as _

from horizon import api
from horizon import exceptions
from horizon import forms
from horizon import tabs
from .forms import UpdateInstance
from .tabs import InstanceDetailTabs


LOG = logging.getLogger(__name__)


def console(request, instance_id):
    try:
        # TODO(jakedahn): clean this up once the api supports tailing.
        data = api.server_console_output(request, instance_id)
    except:
        data = _('Unable to get log for instance "%s".') % instance_id
        exceptions.handle(request, ignore=True)
    response = http.HttpResponse(mimetype='text/plain')
    response.write(data)
    response.flush()
    return response


def vnc(request, instance_id):
    try:
        console = api.server_vnc_console(request, instance_id)
        instance = api.server_get(request, instance_id)
        return shortcuts.redirect(console.url +
                ("&title=%s(%s)" % (instance.name, instance_id)))
    except:
        redirect = reverse("horizon:nova:instances_and_volumes:index")
        msg = _('Unable to get VNC console for instance "%s".') % instance_id
        exceptions.handle(request, msg, redirect=redirect)


class UpdateView(forms.ModalFormView):
    form_class = UpdateInstance
    template_name = 'nova/instances_and_volumes/instances/update.html'
    context_object_name = 'instance'

    def get_object(self, *args, **kwargs):
        if not hasattr(self, "object"):
            instance_id = self.kwargs['instance_id']
            try:
                self.object = api.server_get(self.request, instance_id)
            except:
                redirect = reverse("horizon:nova:instances_and_volumes:index")
                msg = _('Unable to retrieve instance details.')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self.object

    def get_initial(self):
        return {'instance': self.kwargs['instance_id'],
                'tenant_id': self.request.user.tenant_id,
                'name': getattr(self.object, 'name', '')}


class DetailView(tabs.TabView):
    tab_group_class = InstanceDetailTabs
    template_name = 'nova/instances_and_volumes/instances/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["instance"] = self.get_data()
        return context

    def get_data(self):
        if not hasattr(self, "_instance"):
            try:
                instance_id = self.kwargs['instance_id']
                instance = api.server_get(self.request, instance_id)
                instance.volumes = api.volume_instance_list(self.request,
                                                            instance_id)
                # Gather our flavors and images and correlate our instances to
                # them. Exception handling happens in the parent class.
                flavors = api.flavor_list(self.request)
                full_flavors = SortedDict([(str(flavor.id), flavor) for \
                                            flavor in flavors])
                instance.full_flavor = full_flavors[instance.flavor["id"]]
            except:
                redirect = reverse('horizon:nova:instances_and_volumes:index')
                exceptions.handle(self.request,
                                  _('Unable to retrieve details for '
                                    'instance "%s".') % instance_id,
                                    redirect=redirect)
            self._instance = instance
        return self._instance

    def get_tabs(self, request, *args, **kwargs):
        instance = self.get_data()
        return self.tab_group_class(request, instance=instance, **kwargs)
