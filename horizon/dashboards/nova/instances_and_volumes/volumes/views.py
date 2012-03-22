# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
Views for managing Nova volumes.
"""

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from .forms import CreateForm, AttachForm, CreateSnapshotForm
from .tables import AttachmentsTable
from .tabs import VolumeDetailTabs


LOG = logging.getLogger(__name__)


class DetailView(tabs.TabView):
    tab_group_class = VolumeDetailTabs
    template_name = 'nova/instances_and_volumes/volumes/detail.html'


class CreateView(forms.ModalFormView):
    form_class = CreateForm
    template_name = 'nova/instances_and_volumes/volumes/create.html'


class CreateSnapshotView(forms.ModalFormView):
    form_class = CreateSnapshotForm
    template_name = 'nova/instances_and_volumes/volumes/create_snapshot.html'

    def get_context_data(self, **kwargs):
        return {'volume_id': kwargs['volume_id']}

    def get_initial(self):
        return {'volume_id': self.kwargs["volume_id"]}


class EditAttachmentsView(tables.DataTableView):
    table_class = AttachmentsTable
    template_name = 'nova/instances_and_volumes/volumes/attach.html'

    def get_object(self):
        if not hasattr(self, "_object"):
            volume_id = self.kwargs['volume_id']
            try:
                self._object = api.volume_get(self.request, volume_id)
            except:
                self._object = None
                exceptions.handle(self.request,
                                  _('Unable to retrieve volume information.'))
        return self._object

    def get_data(self):
        try:
            volumes = self.get_object()
            attachments = [att for att in volumes.attachments if att]
        except:
            attachments = []
            exceptions.handle(self.request,
                              _('Unable to retrieve volume information.'))
        return attachments

    def get_context_data(self, **kwargs):
        context = super(EditAttachmentsView, self).get_context_data(**kwargs)
        context['form'] = self.form
        context['volume'] = self.get_object()
        return context

    def handle_form(self):
        instances = api.nova.server_list(self.request)
        initial = {'volume_id': self.kwargs["volume_id"],
                   'instances': instances}
        return AttachForm.maybe_handle(self.request, initial=initial)

    def get(self, request, *args, **kwargs):
        self.form, handled = self.handle_form()
        if handled:
            return handled
        handled = self.construct_tables()
        if handled:
            return handled
        context = self.get_context_data(**kwargs)
        context['form'] = self.form
        if request.is_ajax():
            context['hide'] = True
            self.template_name = ('nova/instances_and_volumes/volumes'
                                 '/_attach.html')
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form, handled = self.handle_form()
        if handled:
            return handled
        return super(EditAttachmentsView, self).post(request, *args, **kwargs)
