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

from collections import OrderedDict
import json

from django import shortcuts
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils import encoding
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views import generic

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard.api import cinder
from openstack_dashboard.api import nova
from openstack_dashboard import exceptions as dashboard_exception
from openstack_dashboard.usage import quotas
from openstack_dashboard.utils import filters
from openstack_dashboard.utils import futurist_utils

from openstack_dashboard.dashboards.project.volumes \
    import forms as volume_forms
from openstack_dashboard.dashboards.project.volumes \
    import tables as volume_tables
from openstack_dashboard.dashboards.project.volumes \
    import tabs as project_tabs


class VolumeTableMixIn(object):
    _has_more_data = False
    _has_prev_data = False

    def _get_volumes(self, search_opts=None):
        try:
            marker, sort_dir = self._get_marker()
            volumes, self._has_more_data, self._has_prev_data = \
                cinder.volume_list_paged(self.request, marker=marker,
                                         search_opts=search_opts,
                                         sort_dir=sort_dir, paginate=True)
            return volumes
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve volume list.'))
            return []

    def _get_instances(self, search_opts=None):
        try:
            # TODO(tsufiev): we should pass attached_instance_ids to
            # nova.server_list as soon as Nova API allows for this
            instances, has_more = nova.server_list(self.request,
                                                   search_opts=search_opts)
            return instances
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve volume/instance "
                                "attachment information"))
            return []

    def _get_volumes_ids_with_snapshots(self, search_opts=None):
        try:
            volume_ids = []
            snapshots = cinder.volume_snapshot_list(
                self.request, search_opts=search_opts)
            if snapshots:
                # extract out the volume ids
                volume_ids = set(s.volume_id for s in snapshots)
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve snapshot list."))

        return volume_ids

    def _get_attached_instance_ids(self, volumes):
        attached_instance_ids = []
        for volume in volumes:
            for att in volume.attachments:
                server_id = att.get('server_id', None)
                if server_id is not None:
                    attached_instance_ids.append(server_id)
        return attached_instance_ids

    def _get_groups(self, volumes, search_opts=None):
        needs_group = False
        if volumes and hasattr(volumes[0], 'group_id'):
            needs_group = True
        if needs_group:
            try:
                groups_list = cinder.group_list(self.request,
                                                search_opts=search_opts)
                groups = dict((g.id, g) for g in groups_list)
            except Exception:
                groups = {}
                exceptions.handle(self.request,
                                  _("Unable to retrieve volume groups"))
        for volume in volumes:
            if needs_group:
                volume.group = groups.get(volume.group_id)
            else:
                volume.group = None

    # set attachment string and if volume has snapshots
    def _set_volume_attributes(self,
                               volumes,
                               instances,
                               volume_ids_with_snapshots):
        instances = OrderedDict([(inst.id, inst) for inst in instances])
        for volume in volumes:
            if volume_ids_with_snapshots:
                if volume.id in volume_ids_with_snapshots:
                    setattr(volume, 'has_snapshot', True)
            if instances:
                for att in volume.attachments:
                    server_id = att.get('server_id', None)
                    att['instance'] = instances.get(server_id, None)


class VolumesView(tables.PagedTableMixin, VolumeTableMixIn,
                  tables.DataTableView):
    table_class = volume_tables.VolumesTable
    page_title = _("Volumes")

    def get_data(self):
        volumes = []
        attached_instance_ids = []
        instances = []
        volume_ids_with_snapshots = []

        def _task_get_volumes():
            volumes.extend(self._get_volumes())
            attached_instance_ids.extend(
                self._get_attached_instance_ids(volumes))

        def _task_get_instances():
            # As long as Nova API does not allow passing attached_instance_ids
            # to nova.server_list, this call can be forged to pass anything
            # != None
            instances.extend(self._get_instances())

            # In volumes tab we don't need to know about the assignment
            # instance-image, therefore fixing it to an empty value
            for instance in instances:
                if hasattr(instance, 'image'):
                    if isinstance(instance.image, dict):
                        instance.image['name'] = "-"

        def _task_get_volumes_snapshots():
            volume_ids_with_snapshots.extend(
                self._get_volumes_ids_with_snapshots())

        futurist_utils.call_functions_parallel(
            _task_get_volumes,
            _task_get_instances,
            _task_get_volumes_snapshots)

        self._set_volume_attributes(
            volumes, instances, volume_ids_with_snapshots)
        self._get_groups(volumes)
        return volumes


class DetailView(tabs.TabbedTableView):
    tab_group_class = project_tabs.VolumeDetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ volume.name|default:volume.id }}"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        volume, snapshots = self.get_data()
        table = volume_tables.VolumesTable(self.request)
        context["volume"] = volume
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(volume)
        choices = volume_tables.VolumesTableBase.STATUS_DISPLAY_CHOICES
        volume.status_label = filters.get_display_label(choices, volume.status)
        return context

    def get_search_opts(self, volume):
        return {'volume_id': volume.id}

    @memoized.memoized_method
    def get_data(self):
        try:
            volume_id = self.kwargs['volume_id']
            volume = cinder.volume_get(self.request, volume_id)
            search_opts = self.get_search_opts(volume)
            snapshots = cinder.volume_snapshot_list(
                self.request, search_opts=search_opts)
            if snapshots:
                setattr(volume, 'has_snapshot', True)
            for att in volume.attachments:
                att['instance'] = nova.server_get(self.request,
                                                  att['server_id'])
            if getattr(volume, 'group_id', None):
                volume.group = cinder.group_get(self.request, volume.group_id)
            else:
                volume.group = None
        except Exception:
            redirect = self.get_redirect_url()
            exceptions.handle(self.request,
                              _('Unable to retrieve volume details.'),
                              redirect=redirect)
        try:
            volume.messages = cinder.message_list(
                self.request,
                {'resource_type': 'volume', 'resource_uuid': volume.id},
            )
        except Exception:
            volume.messages = []
            exceptions.handle(
                self.request,
                _('Unable to retrieve volume messages.'),
                ignore=True,
            )
        return volume, snapshots

    def get_redirect_url(self):
        return reverse('horizon:project:volumes:index')

    def get_tabs(self, request, *args, **kwargs):
        volume, snapshots = self.get_data()
        return self.tab_group_class(
            request, volume=volume, snapshots=snapshots, **kwargs)


class CreateView(forms.ModalFormView):
    form_class = volume_forms.CreateForm
    template_name = 'project/volumes/create.html'
    submit_label = _("Create Volume")
    submit_url = reverse_lazy("horizon:project:volumes:create")
    success_url = reverse_lazy('horizon:project:volumes:index')
    page_title = _("Create Volume")

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
            context['usages'] = quotas.tenant_quota_usages(
                self.request, targets=('volumes', 'gigabytes'))
            context['volume_types'] = self._get_volume_types()
        except Exception:
            exceptions.handle(self.request)
        return context

    def _get_volume_types(self):
        volume_types = []
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

        type_descriptions = [{'name': '',
                              'description': no_type_description}] + \
                            [{'name': type.name,
                              'description': getattr(type, "description", "")}
                             for type in volume_types]

        return json.dumps(type_descriptions)


class ExtendView(forms.ModalFormView):
    form_class = volume_forms.ExtendForm
    template_name = 'project/volumes/extend.html'
    submit_label = _("Extend Volume")
    submit_url = "horizon:project:volumes:extend"
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
            usages = quotas.tenant_quota_usages(self.request,
                                                targets=('gigabytes',))
            usages.tally('gigabytes', - context['volume'].size)
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
    form_class = volume_forms.CreateSnapshotForm
    template_name = 'project/volumes/create_snapshot.html'
    submit_url = "horizon:project:volumes:create_snapshot"
    success_url = reverse_lazy('horizon:project:snapshots:index')
    page_title = _("Create Volume Snapshot")

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
            context['usages'] = quotas.tenant_quota_usages(
                self.request, targets=('snapshots', 'gigabytes'))
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve volume information.'))
        return context

    def get_initial(self):
        return {'volume_id': self.kwargs["volume_id"]}


class UploadToImageView(forms.ModalFormView):
    form_class = volume_forms.UploadToImageForm
    template_name = 'project/volumes/upload_to_image.html'
    submit_label = _("Upload")
    submit_url = "horizon:project:volumes:upload_to_image"
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
    form_class = volume_forms.CreateTransferForm
    template_name = 'project/volumes/create_transfer.html'
    success_url = reverse_lazy('horizon:project:volumes:index')
    modal_id = "create_volume_transfer_modal"
    submit_label = _("Create Volume Transfer")
    submit_url = "horizon:project:volumes:create_transfer"
    page_title = _("Create Volume Transfer")

    def get_context_data(self, *args, **kwargs):
        context = super(CreateTransferView, self).get_context_data(**kwargs)
        volume_id = self.kwargs['volume_id']
        context['volume_id'] = volume_id
        context['submit_url'] = reverse(self.submit_url, args=[volume_id])
        return context

    def get_initial(self):
        return {'volume_id': self.kwargs["volume_id"]}

    def get_form_kwargs(self):
        kwargs = super(CreateTransferView, self).get_form_kwargs()
        kwargs['next_view'] = ShowTransferView
        return kwargs


class AcceptTransferView(forms.ModalFormView):
    form_class = volume_forms.AcceptTransferForm
    template_name = 'project/volumes/accept_transfer.html'
    success_url = reverse_lazy('horizon:project:volumes:index')
    modal_id = "accept_volume_transfer_modal"
    submit_label = _("Accept Volume Transfer")
    submit_url = reverse_lazy(
        "horizon:project:volumes:accept_transfer")
    page_title = _("Accept Volume Transfer")


class ShowTransferView(forms.ModalFormView):
    form_class = volume_forms.ShowTransferForm
    template_name = 'project/volumes/show_transfer.html'
    success_url = reverse_lazy('horizon:project:volumes:index')
    modal_id = "show_volume_transfer_modal"
    modal_header = _("Volume Transfer")
    submit_url = "horizon:project:volumes:show_transfer"
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
        context['download_label'] = self.download_label
        context['download_url'] = reverse(
            'horizon:project:volumes:download_transfer_creds',
            args=[context['transfer_id'], context['auth_key']]
        )
        return context

    def get_initial(self):
        transfer = self.get_object()
        return {'id': transfer.id,
                'name': transfer.name,
                'auth_key': self.kwargs['auth_key']}


class UpdateView(forms.ModalFormView):
    form_class = volume_forms.UpdateForm
    modal_id = "update_volume_modal"
    template_name = 'project/volumes/update.html'
    submit_url = "horizon:project:volumes:update"
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
    table_class = volume_tables.AttachmentsTable
    form_class = volume_forms.AttachForm
    form_id = "attach_volume_form"
    modal_id = "attach_volume_modal"
    template_name = 'project/volumes/attach.html'
    submit_url = "horizon:project:volumes:attach"
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
            instances, has_more = nova.server_list(self.request)
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
    form_class = volume_forms.RetypeForm
    modal_id = "retype_volume_modal"
    template_name = 'project/volumes/retype.html'
    submit_label = _("Change Volume Type")
    submit_url = "horizon:project:volumes:retype"
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
    template_name = 'project/volumes/encryption_detail.html'
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
    @method_decorator(never_cache)
    def get(self, request, transfer_id, auth_key):
        try:
            transfer = cinder.transfer_get(self.request, transfer_id)
        except Exception:
            transfer = None
        context = {'transfer': {
            'name': getattr(transfer, 'name', ''),
            'id': transfer_id,
            'auth_key': auth_key,
        }}
        response = shortcuts.render(
            request,
            'project/volumes/download_transfer_creds.html',
            context, content_type='application/text')
        response['Content-Disposition'] = (
            'attachment; filename=%s.txt' % slugify(transfer_id))
        return response
