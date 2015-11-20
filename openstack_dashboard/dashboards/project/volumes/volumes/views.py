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
Views for managing volumes.
"""

import json

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django import http
from django.template.defaultfilters import slugify  # noqa
from django.utils.decorators import method_decorator
from django.utils import encoding
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import never_cache
from django.views import generic

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard import exceptions as dashboard_exception
from openstack_dashboard.usage import quotas
from openstack_dashboard.utils import filters

from openstack_dashboard.dashboards.project.volumes \
    .volumes import forms as project_forms

from openstack_dashboard.dashboards.project.volumes \
    .volumes import tables as project_tables
from openstack_dashboard.dashboards.project.volumes \
    .volumes import tabs as project_tabs


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.VolumeDetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ volume.name|default:volume.id }}"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        volume = self.get_data()
        table = project_tables.VolumesTable(self.request)
        context["volume"] = volume
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(volume)
        choices = project_tables.VolumesTableBase.STATUS_DISPLAY_CHOICES
        volume.status_label = filters.get_display_label(choices, volume.status)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            volume_id = self.kwargs['volume_id']
            volume = cinder.volume_get(self.request, volume_id)
            snapshots = cinder.volume_snapshot_list(
                self.request, search_opts={'volume_id': volume.id})
            if snapshots:
                setattr(volume, 'has_snapshot', True)
            for att in volume.attachments:
                att['instance'] = api.nova.server_get(self.request,
                                                      att['server_id'])
        except Exception:
            redirect = self.get_redirect_url()
            exceptions.handle(self.request,
                              _('Unable to retrieve volume details.'),
                              redirect=redirect)
        return volume

    def get_redirect_url(self):
        return reverse('horizon:project:volumes:index')

    def get_tabs(self, request, *args, **kwargs):
        volume = self.get_data()
        return self.tab_group_class(request, volume=volume, **kwargs)


class CreateView(forms.ModalFormView):
    form_class = project_forms.CreateForm
    modal_header = _("Create Volume")
    template_name = 'project/volumes/volumes/create.html'
    submit_label = _("Create Volume")
    submit_url = reverse_lazy("horizon:project:volumes:volumes:create")
    success_url = reverse_lazy('horizon:project:volumes:volumes_tab')
    page_title = _("Create a Volume")

    def get_initial(self):
        initial = super(CreateView, self).get_initial()
        self.default_vol_type = None
        try:
            self.default_vol_type = cinder.volume_type_default(self.request)
            initial['type'] = self.default_vol_type.name
        except dashboard_exception.NOT_FOUND:
            pass
        return initial

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        try:
            context['usages'] = quotas.tenant_limit_usages(self.request)
            context['volume_types'] = self._get_volume_types()
        except Exception:
            exceptions.handle(self.request)
        return context

    def _get_volume_types(self):
        try:
            volume_types = cinder.volume_type_list(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve volume type list.'))

        # check if we have default volume type so we can present the
        # description of no volume type differently
        no_type_description = None
        if self.default_vol_type is None:
            message = \
                _("If \"No volume type\" is selected, the volume will be "
                  "created without a volume type.")

            no_type_description = encoding.force_text(message)

        type_descriptions = [{'name': 'no_type',
                              'description': no_type_description}] + \
                            [{'name': type.name,
                              'description': getattr(type, "description", "")}
                             for type in volume_types]

        return json.dumps(type_descriptions)


class ExtendView(forms.ModalFormView):
    form_class = project_forms.ExtendForm
    modal_header = _("Extend Volume")
    template_name = 'project/volumes/volumes/extend.html'
    submit_label = _("Extend Volume")
    submit_url = "horizon:project:volumes:volumes:extend"
    success_url = reverse_lazy("horizon:project:volumes:index")
    page_title = _("Extend Volume")

    def get_object(self):
        if not hasattr(self, "_object"):
            volume_id = self.kwargs['volume_id']
            try:
                self._object = cinder.volume_get(self.request, volume_id)
            except Exception:
                self._object = None
                exceptions.handle(self.request,
                                  _('Unable to retrieve volume information.'))
        return self._object

    def get_context_data(self, **kwargs):
        context = super(ExtendView, self).get_context_data(**kwargs)
        context['volume'] = self.get_object()
        args = (self.kwargs['volume_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        try:
            usages = quotas.tenant_limit_usages(self.request)
            usages['gigabytesUsed'] = (usages['gigabytesUsed']
                                       - context['volume'].size)
            context['usages'] = usages
        except Exception:
            exceptions.handle(self.request)
        return context

    def get_initial(self):
        volume = self.get_object()
        return {'id': self.kwargs['volume_id'],
                'name': volume.name,
                'orig_size': volume.size}


class CreateSnapshotView(forms.ModalFormView):
    form_class = project_forms.CreateSnapshotForm
    modal_header = _("Create Volume Snapshot")
    template_name = 'project/volumes/volumes/create_snapshot.html'
    submit_url = "horizon:project:volumes:volumes:create_snapshot"
    success_url = reverse_lazy('horizon:project:volumes:snapshots_tab')
    page_title = _("Create a Volume Snapshot")

    def get_context_data(self, **kwargs):
        context = super(CreateSnapshotView, self).get_context_data(**kwargs)
        context['volume_id'] = self.kwargs['volume_id']
        args = (self.kwargs['volume_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        try:
            volume = cinder.volume_get(self.request, context['volume_id'])
            if (volume.status == 'in-use'):
                context['attached'] = True
                context['form'].set_warning(_("This volume is currently "
                                              "attached to an instance. "
                                              "In some cases, creating a "
                                              "snapshot from an attached "
                                              "volume can result in a "
                                              "corrupted snapshot."))
            context['usages'] = quotas.tenant_limit_usages(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve volume information.'))
        return context

    def get_initial(self):
        return {'volume_id': self.kwargs["volume_id"]}


class UploadToImageView(forms.ModalFormView):
    form_class = project_forms.UploadToImageForm
    modal_header = _("Upload Volume to Image")
    template_name = 'project/volumes/volumes/upload_to_image.html'
    submit_label = _("Upload")
    submit_url = "horizon:project:volumes:volumes:upload_to_image"
    success_url = reverse_lazy("horizon:project:volumes:index")
    page_title = _("Upload Volume to Image")

    @memoized.memoized_method
    def get_data(self):
        try:
            volume_id = self.kwargs['volume_id']
            volume = cinder.volume_get(self.request, volume_id)
        except Exception:
            error_message = _(
                'Unable to retrieve volume information for volume: "%s"') \
                % volume_id
            exceptions.handle(self.request,
                              error_message,
                              redirect=self.success_url)

        return volume

    def get_context_data(self, **kwargs):
        context = super(UploadToImageView, self).get_context_data(**kwargs)
        context['volume'] = self.get_data()
        args = (self.kwargs['volume_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        volume = self.get_data()

        return {'id': self.kwargs['volume_id'],
                'name': volume.name,
                'status': volume.status}


class CreateTransferView(forms.ModalFormView):
    form_class = project_forms.CreateTransferForm
    template_name = 'project/volumes/volumes/create_transfer.html'
    success_url = reverse_lazy('horizon:project:volumes:volumes_tab')
    modal_id = "create_volume_transfer_modal"
    modal_header = _("Create Volume Transfer")
    submit_label = _("Create Volume Transfer")
    submit_url = "horizon:project:volumes:volumes:create_transfer"
    page_title = _("Create a Volume Transfer")

    def get_context_data(self, *args, **kwargs):
        context = super(CreateTransferView, self).get_context_data(**kwargs)
        volume_id = self.kwargs['volume_id']
        context['volume_id'] = volume_id
        context['submit_url'] = reverse(self.submit_url, args=[volume_id])
        return context

    def get_initial(self):
        return {'volume_id': self.kwargs["volume_id"]}


class AcceptTransferView(forms.ModalFormView):
    form_class = project_forms.AcceptTransferForm
    template_name = 'project/volumes/volumes/accept_transfer.html'
    success_url = reverse_lazy('horizon:project:volumes:volumes_tab')
    modal_id = "accept_volume_transfer_modal"
    modal_header = _("Accept Volume Transfer")
    submit_label = _("Accept Volume Transfer")
    submit_url = reverse_lazy(
        "horizon:project:volumes:volumes:accept_transfer")
    page_title = _("Accept Volume Transfer")


class ShowTransferView(forms.ModalFormView):
    form_class = project_forms.ShowTransferForm
    template_name = 'project/volumes/volumes/show_transfer.html'
    success_url = reverse_lazy('horizon:project:volumes:volumes_tab')
    modal_id = "show_volume_transfer_modal"
    modal_header = _("Volume Transfer")
    submit_url = "horizon:project:volumes:volumes:show_transfer"
    cancel_label = _("Close")
    download_label = _("Download transfer credentials")
    page_title = _("Volume Transfer Details")

    def get_object(self):
        try:
            return self._object
        except AttributeError:
            transfer_id = self.kwargs['transfer_id']
            try:
                self._object = cinder.transfer_get(self.request, transfer_id)
                return self._object
            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to retrieve volume transfer.'))

    def get_context_data(self, **kwargs):
        context = super(ShowTransferView, self).get_context_data(**kwargs)
        context['transfer_id'] = self.kwargs['transfer_id']
        context['auth_key'] = self.kwargs['auth_key']
        context['submit_url'] = reverse(self.submit_url, args=[
            context['transfer_id'], context['auth_key']])
        context['download_label'] = self.download_label
        context['download_url'] = reverse(
            'horizon:project:volumes:volumes:download_transfer_creds',
            args=[context['transfer_id'], context['auth_key']]
        )
        return context

    def get_initial(self):
        transfer = self.get_object()
        return {'id': transfer.id,
                'name': transfer.name,
                'auth_key': self.kwargs['auth_key']}


class UpdateView(forms.ModalFormView):
    form_class = project_forms.UpdateForm
    modal_header = _("Edit Volume")
    modal_id = "update_volume_modal"
    template_name = 'project/volumes/volumes/update.html'
    submit_url = "horizon:project:volumes:volumes:update"
    success_url = reverse_lazy("horizon:project:volumes:index")
    page_title = _("Edit Volume")

    def get_object(self):
        if not hasattr(self, "_object"):
            vol_id = self.kwargs['volume_id']
            try:
                self._object = cinder.volume_get(self.request, vol_id)
            except Exception:
                msg = _('Unable to retrieve volume.')
                url = reverse('horizon:project:volumes:index')
                exceptions.handle(self.request, msg, redirect=url)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['volume'] = self.get_object()
        args = (self.kwargs['volume_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        volume = self.get_object()
        return {'volume_id': self.kwargs["volume_id"],
                'name': volume.name,
                'description': volume.description,
                'bootable': volume.is_bootable}


class EditAttachmentsView(tables.DataTableView, forms.ModalFormView):
    table_class = project_tables.AttachmentsTable
    form_class = project_forms.AttachForm
    form_id = "attach_volume_form"
    modal_header = _("Manage Volume Attachments")
    modal_id = "attach_volume_modal"
    template_name = 'project/volumes/volumes/attach.html'
    submit_url = "horizon:project:volumes:volumes:attach"
    success_url = reverse_lazy("horizon:project:volumes:index")
    page_title = _("Manage Volume Attachments")

    @memoized.memoized_method
    def get_object(self):
        volume_id = self.kwargs['volume_id']
        try:
            return cinder.volume_get(self.request, volume_id)
        except Exception:
            self._object = None
            exceptions.handle(self.request,
                              _('Unable to retrieve volume information.'))

    def get_data(self):
        attachments = []
        volume = self.get_object()
        if volume is not None:
            for att in volume.attachments:
                att['volume_name'] = getattr(volume, 'name', att['device'])
                attachments.append(att)
        return attachments

    def get_initial(self):
        try:
            instances, has_more = api.nova.server_list(self.request)
        except Exception:
            instances = []
            exceptions.handle(self.request,
                              _("Unable to retrieve attachment information."))
        return {'volume': self.get_object(),
                'instances': instances}

    @memoized.memoized_method
    def get_form(self, **kwargs):
        form_class = kwargs.get('form_class', self.get_form_class())
        return super(EditAttachmentsView, self).get_form(form_class)

    def get_context_data(self, **kwargs):
        context = super(EditAttachmentsView, self).get_context_data(**kwargs)
        context['form'] = self.get_form()
        volume = self.get_object()
        args = (self.kwargs['volume_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        if volume and volume.status == 'available':
            context['show_attach'] = True
        else:
            context['show_attach'] = False
        context['volume'] = volume
        if self.request.is_ajax():
            context['hide'] = True
        return context

    def get(self, request, *args, **kwargs):
        # Table action handling
        handled = self.construct_tables()
        if handled:
            return handled
        return self.render_to_response(self.get_context_data(**kwargs))

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.get(request, *args, **kwargs)


class RetypeView(forms.ModalFormView):
    form_class = project_forms.RetypeForm
    modal_id = "retype_volume_modal"
    modal_header = _("Change Volume Type")
    template_name = 'project/volumes/volumes/retype.html'
    submit_label = _("Change Volume Type")
    submit_url = "horizon:project:volumes:volumes:retype"
    success_url = reverse_lazy("horizon:project:volumes:index")
    page_title = _("Change Volume Type")

    @memoized.memoized_method
    def get_data(self):
        try:
            volume_id = self.kwargs['volume_id']
            volume = cinder.volume_get(self.request, volume_id)
        except Exception:
            error_message = _(
                'Unable to retrieve volume information for volume: "%s"') \
                % volume_id
            exceptions.handle(self.request,
                              error_message,
                              redirect=self.success_url)

        return volume

    def get_context_data(self, **kwargs):
        context = super(RetypeView, self).get_context_data(**kwargs)
        context['volume'] = self.get_data()
        args = (self.kwargs['volume_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        volume = self.get_data()

        return {'id': self.kwargs['volume_id'],
                'name': volume.name,
                'volume_type': volume.volume_type}


class EncryptionDetailView(generic.TemplateView):
    template_name = 'project/volumes/volumes/encryption_detail.html'
    page_title = _("Volume Encryption Details: {{ volume.name }}")

    def get_context_data(self, **kwargs):
        context = super(EncryptionDetailView, self).get_context_data(**kwargs)
        volume = self.get_volume_data()
        context["encryption_metadata"] = self.get_encryption_data()
        context["volume"] = volume
        context["page_title"] = _("Volume Encryption Details: "
                                  "%(volume_name)s") % {'volume_name':
                                                        volume.name}
        return context

    @memoized.memoized_method
    def get_encryption_data(self):
        try:
            volume_id = self.kwargs['volume_id']
            self._encryption_metadata = \
                cinder.volume_get_encryption_metadata(self.request,
                                                      volume_id)
        except Exception:
            redirect = self.get_redirect_url()
            exceptions.handle(self.request,
                              _('Unable to retrieve volume encryption '
                                'details.'),
                              redirect=redirect)
        return self._encryption_metadata

    @memoized.memoized_method
    def get_volume_data(self):
        try:
            volume_id = self.kwargs['volume_id']
            volume = cinder.volume_get(self.request, volume_id)
        except Exception:
            redirect = self.get_redirect_url()
            exceptions.handle(self.request,
                              _('Unable to retrieve volume details.'),
                              redirect=redirect)
        return volume

    def get_redirect_url(self):
        return reverse('horizon:project:volumes:index')


class DownloadTransferCreds(generic.View):
    # TODO(Itxaka): Remove cache_control in django >= 1.9
    # https://code.djangoproject.com/ticket/13008
    @method_decorator(cache_control(max_age=0, no_cache=True,
                                    no_store=True, must_revalidate=True))
    @method_decorator(never_cache)
    def get(self, request, transfer_id, auth_key):
        try:
            transfer = cinder.transfer_get(self.request, transfer_id)
        except Exception:
            transfer = None
        response = http.HttpResponse(content_type='application/text')
        response['Content-Disposition'] = \
            'attachment; filename=%s.txt' % slugify(transfer_id)
        response.write('%s: %s\n%s: %s\n%s: %s' % (
            _("Transfer name"),
            getattr(transfer, 'name', ''),
            _("Transfer ID"),
            transfer_id,
            _("Authorization Key"),
            auth_key))
        response['Content-Length'] = str(len(response.content))
        return response
