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


from django import forms
from django.utils.translation import ugettext as _

from horizon import api
from horizon import exceptions
from horizon import workflows


class UpdateProjectQuotaAction(workflows.Action):
    ifcb_label = _("Injected File Content Bytes")
    metadata_items = forms.IntegerField(min_value=0, label=_("Metadata Items"))
    cores = forms.IntegerField(min_value=0, label=_("VCPUs"))
    instances = forms.IntegerField(min_value=0, label=_("Instances"))
    injected_files = forms.IntegerField(min_value=0, label=_("Injected Files"))
    injected_file_content_bytes = forms.IntegerField(min_value=0,
                                                     label=ifcb_label)
    volumes = forms.IntegerField(min_value=0, label=_("Volumes"))
    gigabytes = forms.IntegerField(min_value=0, label=_("Gigabytes"))
    ram = forms.IntegerField(min_value=0, label=_("RAM (MB)"))
    floating_ips = forms.IntegerField(min_value=0, label=_("Floating IPs"))

    class Meta:
        name = _("Quota")
        slug = 'update_quotas'
        help_text = _("From here you can set quotas "
                      "(max limits) for the project.")


class UpdateProjectQuota(workflows.Step):
    action_class = UpdateProjectQuotaAction
    depends_on = ("project_id",)
    contributes = ("metadata_items",
                   "cores",
                   "instances",
                   "injected_files",
                   "injected_file_content_bytes",
                   "volumes",
                   "gigabytes",
                   "ram",
                   "floating_ips")


class CreateProjectInfoAction(workflows.Action):
    name = forms.CharField(label=_("Name"))
    description = forms.CharField(
            widget=forms.widgets.Textarea(),
            label=_("Description"),
            required=False)
    enabled = forms.BooleanField(label=_("Enabled"),
                                 required=False,
                                 initial=True)

    class Meta:
        name = _("Project Info")
        help_text = _("From here you can create a new "
                      "project to organize users.")


class CreateProjectInfo(workflows.Step):
    action_class = CreateProjectInfoAction
    contributes = ("project_id",
                   "name",
                   "description",
                   "enabled")


class CreateProject(workflows.Workflow):
    slug = "add_project"
    name = _("Add Project")
    finalize_button_name = _("Finish")
    success_message = _('Created new project "%s".')
    failure_message = _('Unable to create project "%s".')
    success_url = "horizon:syspanel:projects:index"
    default_steps = (CreateProjectInfo,
                     UpdateProjectQuota)

    def format_status_message(self, message):
        return message % self.context.get('name', 'unknown project')

    def handle(self, request, data):
        # create the project
        try:
            desc = data['description']
            self.object = api.keystone.tenant_create(request,
                                                     tenant_name=data['name'],
                                                     description=desc,
                                                     enabled=data['enabled'])
        except:
            exceptions.handle(request, ignore=True)
            return False

        # update the project quota
        ifcb = data['injected_file_content_bytes']
        try:
            api.nova.tenant_quota_update(request,
                                         self.object.id,
                                         metadata_items=data['metadata_items'],
                                         injected_file_content_bytes=ifcb,
                                         volumes=data['volumes'],
                                         gigabytes=data['gigabytes'],
                                         ram=data['ram'],
                                         floating_ips=data['floating_ips'],
                                         instances=data['instances'],
                                         injected_files=data['injected_files'],
                                         cores=data['cores'])
        except:
            exceptions.handle(request, _('Unable to set project quotas.'))
        return True


class UpdateProjectInfoAction(CreateProjectInfoAction):
    enabled = forms.BooleanField(required=False, label=_("Enabled"))

    class Meta:
        name = _("Project Info")
        slug = 'update_info'
        help_text = _("From here you can edit the project details.")


class UpdateProjectInfo(workflows.Step):
    action_class = UpdateProjectInfoAction
    depends_on = ("project_id",)
    contributes = ("name",
                   "description",
                   "enabled")


class UpdateProject(workflows.Workflow):
    slug = "update_project"
    name = _("Edit Project")
    finalize_button_name = _("Save")
    success_message = _('Modified project "%s".')
    failure_message = _('Unable to modify project "%s".')
    success_url = "horizon:syspanel:projects:index"
    default_steps = (UpdateProjectInfo,
                     UpdateProjectQuota)

    def format_status_message(self, message):
        return message % self.context.get('name', 'unknown project')

    def handle(self, request, data):

        # update project info
        try:
            api.tenant_update(request,
                              tenant_id=data['project_id'],
                              tenant_name=data['name'],
                              description=data['description'],
                              enabled=data['enabled'])
        except:
            exceptions.handle(request, ignore=True)
            return False

        # update the project quota
        ifcb = data['injected_file_content_bytes']
        try:
            api.tenant_quota_update(request,
                                    data['project_id'],
                                    metadata_items=data['metadata_items'],
                                    injected_file_content_bytes=ifcb,
                                    volumes=data['volumes'],
                                    gigabytes=data['gigabytes'],
                                    ram=data['ram'],
                                    floating_ips=data['floating_ips'],
                                    instances=data['instances'],
                                    injected_files=data['injected_files'],
                                    cores=data['cores'])
            return True
        except:
            exceptions.handle(request, _('Modified project information, but'
                                         'unable to modify project quotas.'))
            return True
