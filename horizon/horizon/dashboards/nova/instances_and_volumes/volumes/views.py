# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 Nebula, Inc.
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

from django import shortcuts
from django.contrib import messages
from django.utils.translation import ugettext as _
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon import exceptions
from horizon import forms
from horizon import tables
from .forms import CreateForm, AttachForm
from .tables import AttachmentsTable


LOG = logging.getLogger(__name__)


def detail(request, volume_id):
    try:
        volume = api.volume_get(request, volume_id)
        attachment = volume.attachments[0]
        if attachment:
            instance = api.server_get(
                    request, volume.attachments[0]['serverId'])
        else:
            instance = None
    except novaclient_exceptions.ClientException, e:
        LOG.exception("ClientException in volume get")
        messages.error(request, _('Error fetching volume: %s') % e.message)
        return shortcuts.redirect(
                            'horizon:nova:instances_and_volumes:volumes:index')

    return shortcuts.render(request,
                            'nova/instances_and_volumes/volumes/detail.html', {
                                'volume': volume,
                                'attachment': attachment,
                                'instance': instance})


class CreateView(forms.ModalFormView):
    form_class = CreateForm
    template_name = 'nova/instances_and_volumes/volumes/create.html'


class EditAttachmentsView(tables.DataTableView):
    table_class = AttachmentsTable
    template_name = 'nova/instances_and_volumes/volumes/attach.html'

    def get_data(self):
        volume_id = self.kwargs['volume_id']
        try:
            self.object = api.volume_get(self.request, volume_id)
            attachments = [att for att in self.object.attachments if att]
        except:
            self.object = None
            attachments = []
            exceptions.handle(self.request,
                              _('Unable to retrieve volume information.'))
        return attachments

    def handle_form(self):
        instances = api.nova.server_list(self.request)
        initial = {'volume_id': self.kwargs["volume_id"],
                   'instances': instances}
        return AttachForm.maybe_handle(self.request, initial=initial)

    def get(self, request, *args, **kwargs):
        form, handled = self.handle_form()
        if handled:
            return handled
        tables = self.get_tables()
        if not self.object:
            return shortcuts.redirect("horizon:nova:instances_and_volumes:"
                                      "index")
        context = self.get_context_data(**kwargs)
        context['form'] = form
        context['volume'] = self.object
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form, handled = self.handle_form()
        if handled:
            return handled
        return super(EditAttachmentsView, self).post(request, *args, **kwargs)
