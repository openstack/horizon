# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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
Forms used by various views.
"""

import re

from django import forms
from django.contrib.auth import models as auth_models
from django.utils.translation import ugettext as _

from django_openstack.nova.exceptions import wrap_nova_error


# TODO: Store this in settings.
MAX_VOLUME_SIZE = 100

alphanumeric_re = re.compile(r'^\w+$')


@wrap_nova_error
def get_instance_type_choices():
    """
    Returns list of instance types from nova admin api
    """
    nova = get_nova_admin_connection()
    instance_types = nova.get_instance_types()
    rv = []
    for t in instance_types:
        rv.append((t.name, "%s (%sMB memory, %s cpu, %sGB space)" % \
                      (t.name, t.memory_mb, t.vcpus, t.disk_gb)))
    return rv


def get_instance_choices(project):
    choices = [(i.id, "%s (%s)" % (i.id, i.displayName))
               for i in project.get_instances()]
    if not len(choices):
        choices = [('', 'none available')]
    return choices


def get_key_pair_choices(project):
    choices = [(k.name, k.name) for k in project.get_key_pairs()]
    if not len(choices):
        choices = [('', _('none available'))]
    return choices

#def get_security_group_choices(project):
#    choices = [(g.name, g.description) for g in project.get_security_groups()]
#    if len(choices) == 0:
#        choices = [('', 'none available')]
#    return choices


def get_available_volume_choices(project):
    choices = [(v.id, '%s %s - %dGB' % (v.id, v.displayName, v.size))
               for v in project.get_volumes() if v.status != 'in-use']
    if not len(choices):
        choices = [('', _('none available'))]
    return choices


def get_protocols():
    return (
        ('tcp', 'tcp'),
        ('udp', 'udp'),
    )


class ProjectFormBase(forms.Form):
    def __init__(self, project, *args, **kwargs):
        self.project = project
        super(ProjectFormBase, self).__init__(*args, **kwargs)


class LaunchInstanceForm(forms.Form):
    # nickname = forms.CharField()
    # description = forms.CharField()

    count = forms.ChoiceField(choices=[(x, x) for x in range(1, 6)])
    size = forms.ChoiceField()
    key_name = forms.ChoiceField()
    user_data = forms.CharField(required=False,
                                widget=forms.widgets.Textarea(
                                    attrs={'rows': 4}))

    def __init__(self, project, *args, **kwargs):
        forms.Form.__init__(self, *args, **kwargs)
        self.fields['key_name'].choices = get_key_pair_choices(project)
        self.fields['size'].choices = get_instance_type_choices()


class UpdateInstanceForm(forms.Form):
    nickname = forms.CharField(required=False, label="Name")
    description = forms.CharField(required=False,
                                  widget=forms.Textarea,
                                  max_length=70)

    def __init__(self, instance, *args, **kwargs):
        forms.Form.__init__(self, *args, **kwargs)
        self.fields['nickname'].initial = instance.displayName
        self.fields['description'].initial = instance.displayDescription


class UpdateImageForm(forms.Form):
    nickname = forms.CharField(required=False, label="Name")
    description = forms.CharField(required=False,
                                  widget=forms.Textarea,
                                  max_length=70)

    def __init__(self, image, *args, **kwargs):
        forms.Form.__init__(self, *args, **kwargs)
        self.fields['nickname'].initial = image.displayName
        self.fields['description'].initial = image.description


class CreateVolumeForm(forms.Form):
    size = forms.IntegerField(label='Size (in GB)',
                              min_value=1,
                              max_value=MAX_VOLUME_SIZE)
    nickname = forms.CharField()
    description = forms.CharField()


class AttachVolumeForm(ProjectFormBase):
    volume = forms.ChoiceField()
    instance = forms.ChoiceField()
    device = forms.CharField(initial='/dev/vdc')

    def __init__(self, project, *args, **kwargs):
        super(AttachVolumeForm, self).__init__(project, *args, **kwargs)
        self.fields['volume'].choices = get_available_volume_choices(project)
        self.fields['instance'].choices = get_instance_choices(project)




class LaunchForm(forms.Form):
    image_id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=80, label="Server Name")

    # make the dropdown populate when the form is loaded not when django is
    # started
    def __init__(self, *args, **kwargs):
        super(LaunchForm, self).__init__(*args, **kwargs)
        flavorlist = kwargs.get('initial', {}).get('flavorlist', [])
        self.fields['flavor'] = forms.ChoiceField(
                choices=flavorlist,
                label="Flavor",
                help_text="Size of Image to launch")


class UploadImageForm(forms.Form):
    name = forms.CharField(max_length="5", label="Name")
    image_file = forms.FileField(required=False)
    is_public = forms.BooleanField(label="Publicly Available", required=False)


