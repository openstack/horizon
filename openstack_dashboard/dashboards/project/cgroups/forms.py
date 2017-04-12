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


from django.core.urlresolvers import reverse
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

    def clean(self):
        cleaned_data = super(UpdateForm, self).clean()
        new_desc = cleaned_data.get('description')
        old_desc = self.initial['description']
        if old_desc and not new_desc:
            error_msg = _("Description is required.")
            self._errors['description'] = self.error_class([error_msg])
            return cleaned_data

        return cleaned_data

    def handle(self, request, data):
        cgroup_id = self.initial['cgroup_id']

        try:
            cinder.volume_cgroup_update(request,
                                        cgroup_id,
                                        data['name'],
                                        data['description'])

            message = _('Updating volume consistency '
                        'group "%s"') % data['name']
            messages.info(request, message)
            return True
        except Exception:
            redirect = reverse("horizon:project:cgroups:index")
            exceptions.handle(request,
                              _('Unable to update volume consistency group.'),
                              redirect=redirect)


class RemoveVolsForm(forms.SelfHandlingForm):
    def handle(self, request, data):
        cgroup_id = self.initial['cgroup_id']
        name = self.initial['name']
        search_opts = {'consistencygroup_id': cgroup_id}

        try:
            # get list of assigned volumes
            assigned_vols = []
            volumes = cinder.volume_list(request,
                                         search_opts=search_opts)
            for volume in volumes:
                assigned_vols.append(volume.id)

            assigned_vols_str = ",".join(assigned_vols)
            cinder.volume_cgroup_update(request,
                                        cgroup_id,
                                        remove_vols=assigned_vols_str)

            message = _('Removing volumes from volume consistency '
                        'group "%s"') % name
            messages.info(request, message)
            return True

        except Exception:
            redirect = reverse("horizon:project:cgroups:index")
            exceptions.handle(request, _('Errors occurred in removing volumes '
                                         'from consistency group.'),
                              redirect=redirect)


class DeleteForm(forms.SelfHandlingForm):
    delete_volumes = forms.BooleanField(label=_("Delete Volumes"),
                                        required=False)

    def handle(self, request, data):
        cgroup_id = self.initial['cgroup_id']
        name = self.initial['name']
        delete_volumes = data['delete_volumes']

        try:
            cinder.volume_cgroup_delete(request,
                                        cgroup_id,
                                        force=delete_volumes)
            message = _('Deleting volume consistency '
                        'group "%s"') % name
            messages.success(request, message)
            return True

        except Exception:
            redirect = reverse("horizon:project:cgroups:index")
            exceptions.handle(request, _('Errors occurred in deleting '
                                         'consistency group.'),
                              redirect=redirect)


class CreateSnapshotForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255, label=_("Snapshot Name"))
    description = forms.CharField(max_length=255,
                                  widget=forms.Textarea(attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)

    def __init__(self, request, *args, **kwargs):
        super(CreateSnapshotForm, self).__init__(request, *args, **kwargs)

        # populate cgroup_id
        cgroup_id = kwargs.get('initial', {}).get('cgroup_id', [])
        self.fields['cgroup_id'] = forms.CharField(widget=forms.HiddenInput(),
                                                   initial=cgroup_id)

    def handle(self, request, data):
        try:
            message = _('Creating consistency group snapshot "%s".') \
                % data['name']
            snapshot = cinder.volume_cg_snapshot_create(request,
                                                        data['cgroup_id'],
                                                        data['name'],
                                                        data['description'])

            messages.info(request, message)
            return snapshot
        except Exception as e:
            redirect = reverse("horizon:project:cgroups:index")
            msg = _('Unable to create consistency group snapshot.')
            if e.code == 413:
                msg = _('Requested snapshot would exceed the allowed quota.')
            else:
                search_opts = {'consistentcygroup_id': data['cgroup_id']}
                volumes = cinder.volume_list(request, search_opts=search_opts)
                if len(volumes) == 0:
                    msg = _('Unable to create snapshot. Consistency group '
                            'must contain volumes.')

            exceptions.handle(request,
                              msg,
                              redirect=redirect)


class CloneCGroupForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255, label=_("Consistency Group Name"))
    description = forms.CharField(max_length=255,
                                  widget=forms.Textarea(attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)
    cgroup_source = forms.ChoiceField(
        label=_("Use a consistency group as source"),
        widget=forms.ThemableSelectWidget(
            attrs={'class': 'image-selector'},
            data_attrs=('name'),
            transform=lambda x: "%s" % (x.name)),
        required=False)

    def prepare_cgroup_source_field(self, request, cgroup_id):
        try:
            cgroup = cinder.volume_cgroup_get(request,
                                              cgroup_id)
            self.fields['cgroup_source'].choices = ((cgroup_id,
                                                     cgroup),)
        except Exception:
            exceptions.handle(request, _('Unable to load the specified '
                                         'consistency group.'))

    def __init__(self, request, *args, **kwargs):
        super(CloneCGroupForm, self).__init__(request, *args, **kwargs)

        # populate cgroup_id
        cgroup_id = kwargs.get('initial', {}).get('cgroup_id', [])
        self.fields['cgroup_id'] = forms.CharField(widget=forms.HiddenInput(),
                                                   initial=cgroup_id)
        self.prepare_cgroup_source_field(request, cgroup_id)

    def handle(self, request, data):
        try:
            message = _('Creating consistency group "%s".') % data['name']
            cgroup = cinder.volume_cgroup_create_from_source(
                request,
                data['name'],
                source_cgroup_id=data['cgroup_id'],
                description=data['description'])

            messages.info(request, message)
            return cgroup
        except Exception:
            redirect = reverse("horizon:project:cgroups:index")
            msg = _('Unable to clone consistency group.')

            search_opts = {'consistentcygroup_id': data['cgroup_id']}
            volumes = cinder.volume_list(request, search_opts=search_opts)
            if len(volumes) == 0:
                msg = _('Unable to clone empty consistency group.')

            exceptions.handle(request,
                              msg,
                              redirect=redirect)
