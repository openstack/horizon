# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.api import cinder


class UpdateForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255, label=_("Name"))
    description = forms.CharField(max_length=255,
                                  widget=forms.Textarea(attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)

    def handle(self, request, data):
        group_id = self.initial['group_id']

        try:
            cinder.group_update(request, group_id,
                                data['name'],
                                data['description'])

            message = _('Updating volume group "%s"') % data['name']
            messages.info(request, message)
            return True
        except Exception:
            redirect = reverse("horizon:project:volume_groups:index")
            exceptions.handle(request,
                              _('Unable to update volume group.'),
                              redirect=redirect)


class RemoveVolsForm(forms.SelfHandlingForm):
    failure_url = 'horizon:project:volume_groups:index'

    def handle(self, request, data):
        group_id = self.initial['group_id']
        name = self.initial['name']
        search_opts = {'group_id': group_id}

        try:
            # get list of assigned volumes
            assigned_vols = []
            volumes = cinder.volume_list(request,
                                         search_opts=search_opts)
            for volume in volumes:
                assigned_vols.append(volume.id)

            cinder.group_update(request, group_id,
                                remove_volumes=assigned_vols)

            message = _('Removing volumes from volume group "%s"') % name
            messages.info(request, message)
            return True

        except Exception:
            redirect = reverse(self.failure_url)
            exceptions.handle(request,
                              _('Errors occurred in removing volumes '
                                'from group.'),
                              redirect=redirect)


class DeleteForm(forms.SelfHandlingForm):
    delete_volumes = forms.BooleanField(label=_("Delete Volumes"),
                                        required=False)
    failure_url = 'horizon:project:volume_groups:index'

    def handle(self, request, data):
        group_id = self.initial['group_id']
        name = self.initial['name']
        delete_volumes = data['delete_volumes']

        try:
            cinder.group_delete(request, group_id,
                                delete_volumes=delete_volumes)
            message = _('Deleting volume group "%s"') % name
            messages.success(request, message)
            return True

        except Exception:
            redirect = reverse(self.failure_url)
            exceptions.handle(request, _('Errors occurred in deleting group.'),
                              redirect=redirect)


class CreateSnapshotForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255, label=_("Snapshot Name"))
    description = forms.CharField(max_length=255,
                                  widget=forms.Textarea(attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)

    def handle(self, request, data):
        group_id = self.initial['group_id']
        try:
            message = _('Creating group snapshot "%s".') \
                % data['name']
            snapshot = cinder.group_snapshot_create(request,
                                                    group_id,
                                                    data['name'],
                                                    data['description'])

            messages.info(request, message)
            return snapshot
        except Exception as e:
            redirect = reverse("horizon:project:volume_groups:index")
            msg = _('Unable to create group snapshot.')
            if e.code == 413:
                msg = _('Requested snapshot would exceed the allowed quota.')
            else:
                search_opts = {'group_id': group_id}
                volumes = cinder.volume_list(request,
                                             search_opts=search_opts)
                if not volumes:
                    msg = _('Unable to create snapshot. '
                            'group must contain volumes.')

            exceptions.handle(request,
                              msg,
                              redirect=redirect)


class CloneGroupForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255, label=_("Group Name"))
    description = forms.CharField(max_length=255,
                                  widget=forms.Textarea(attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)
    group_source = forms.ChoiceField(
        label=_("Use a group as source"),
        widget=forms.ThemableSelectWidget(
            attrs={'class': 'image-selector'},
            data_attrs=('name'),
            transform=lambda x: "%s" % (x.name)),
        required=False)

    def prepare_group_source_field(self, request):
        try:
            group_id = self.initial['group_id']
            group = cinder.group_get(request, group_id)
            self.fields['group_source'].choices = ((group_id, group),)
        except Exception:
            exceptions.handle(request,
                              _('Unable to load the specified group.'))

    def __init__(self, request, *args, **kwargs):
        super(CloneGroupForm, self).__init__(request, *args, **kwargs)
        self.prepare_group_source_field(request)

    def handle(self, request, data):
        group_id = self.initial['group_id']
        try:
            message = _('Cloning volume group "%s".') % data['name']
            group = cinder.group_create_from_source(
                request,
                data['name'],
                source_group_id=group_id,
                description=data['description'])

            messages.info(request, message)
            return group
        except Exception:
            redirect = reverse("horizon:project:volume_groups:index")
            msg = _('Unable to clone group.')

            search_opts = {'group_id': group_id}
            volumes = cinder.volume_list(request, search_opts=search_opts)
            if not volumes:
                msg = _('Unable to clone empty group.')

            exceptions.handle(request,
                              msg,
                              redirect=redirect)
