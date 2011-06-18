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

from django_openstack.core.connection import get_nova_admin_connection
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


@wrap_nova_error
def get_roles(project_roles=True):
    nova = get_nova_admin_connection()
    roles = nova.get_roles(project_roles=project_roles)
    return [(role.role, role.role) for role in roles]


@wrap_nova_error
def get_members(project):
    nova = get_nova_admin_connection()
    members = nova.get_project_members(project)
    return [str(user.memberId) for user in members]


@wrap_nova_error
def set_project_roles(projectname, username, roles):
    nova = get_nova_admin_connection()
    # hacky work around to interface correctly with multiple select form
    _remove_roles(projectname, username)

    for role in roles:
        nova.add_user_role(username, str(role), projectname)


def _remove_roles(project, username):
    nova = get_nova_admin_connection()
    userroles = nova.get_user_roles(username,  project)
    roles = [str(role.role) for role in userroles]

    for role in roles:
        if role == "developer":
            nova.remove_user_role(username, "developer", project)
        if role == "sysadmin":
            nova.remove_user_role(username, "sysadmin", project)
        if role == "netadmin":
            nova.remove_user_role(username, "netadmin", project)


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
    display_name = forms.CharField(required=True, label="Name")
    #security_group = forms.ChoiceField()
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


class CreateKeyPairForm(ProjectFormBase):
    name = forms.RegexField(regex=alphanumeric_re)

    def clean_name(self):
        name = self.cleaned_data['name']

        if self.project.has_key_pair(name):
            raise forms.ValidationError(
                    _('A key named %s already exists.') % name)

        return name


class CreateSecurityGroupForm(ProjectFormBase):
    name = forms.RegexField(regex=alphanumeric_re)
    description = forms.CharField()

    def clean_name(self):
        name = self.cleaned_data['name']

        if self.project.has_security_group(name):
            raise forms.ValidationError(
                    _('A security group named %s already exists.') % name)

        return name


class AuthorizeSecurityGroupRuleForm(forms.Form):
    protocol = forms.ChoiceField(choices=get_protocols())
    from_port = forms.IntegerField(min_value=1, max_value=65535)
    to_port = forms.IntegerField(min_value=1, max_value=65535)


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


class ProjectForm(forms.Form):
    projectname = forms.CharField(label="Project Name", max_length=20)
    description = forms.CharField(label="Description",
                                  widget=forms.widgets.Textarea())
    manager = forms.ModelChoiceField(queryset=auth_models.User.objects.all(),
                                     label="Project Manager")


class GlobalRolesForm(forms.Form):
    role = forms.MultipleChoiceField(label='Roles', required=False)

    def __init__(self, *args, **kwargs):
        super(GlobalRolesForm, self).__init__(*args, **kwargs)
        self.fields['role'].choices = get_roles(project_roles=False)


class ProjectUserForm(forms.Form):
    role = forms.MultipleChoiceField(label='Roles', required=False)

    def __init__(self, project, user, *args, **kwargs):
        super(ProjectUserForm, self).__init__(*args, **kwargs)
        self.project = project
        self.user = user
        self.fields['role'].choices = get_roles()

    def save(self):
        set_project_roles(self.project.projectname,
                          self.user.username,
                          self.cleaned_data['role'])


class AddProjectUserForm(forms.Form):
    username = forms.ModelChoiceField(queryset='',
                                      label='Username',
                                      empty_label='Select a Username')
    role = forms.MultipleChoiceField(label='Roles')

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project')
        super(AddProjectUserForm, self).__init__(*args, **kwargs)
        members = get_members(project)

        self.fields['username'].queryset = \
                auth_models.User.objects.exclude(username__in=members)
        self.fields['role'].choices = get_roles()


class SendCredentialsForm(forms.Form):
    users = forms.MultipleChoiceField(label='Users', required=True)

    def __init__(self, *args, **kwargs):
        query_list = kwargs.pop('query_list')
        super(SendCredentialsForm, self).__init__(*args, **kwargs)

        self.fields['users'].choices = \
            [(choices, choices) for choices in query_list]
