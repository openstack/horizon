# Copyright 2013 CentRin Data, Inc.
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


import json

from django.utils import encoding
from django.utils.translation import gettext_lazy as _
from django.views.decorators.debug import sensitive_variables

from horizon import exceptions
from horizon import forms
from horizon import workflows
from openstack_dashboard import api
from openstack_dashboard.dashboards.project.instances \
    import utils as instance_utils


class SetAdvancedAction(workflows.Action):
    disk_config = forms.ThemableChoiceField(
        label=_("Disk Partition"), required=False,
        help_text=_("Automatic: The entire disk is a single partition and "
                    "automatically resizes. Manual: Results in faster build "
                    "times but requires manual partitioning."))
    config_drive = forms.BooleanField(
        label=_("Configuration Drive"),
        required=False, help_text=_("Configure OpenStack to write metadata to "
                                    "a special configuration drive that "
                                    "attaches to the instance when it boots."))

    def __init__(self, request, context, *args, **kwargs):
        super().__init__(request, context, *args, **kwargs)
        try:
            config_choices = [("AUTO", _("Automatic")),
                              ("MANUAL", _("Manual"))]
            self.fields['disk_config'].choices = config_choices

            # Only show the Config Drive option for the Launch Instance
            # is supported.
            if context.get('workflow_slug') != 'launch_instance':
                del self.fields['config_drive']

        except Exception:
            exceptions.handle(request, _('Unable to retrieve extensions '
                                         'information.'))

    class Meta(object):
        name = _("Advanced Options")
        help_text_template = ("project/instances/"
                              "_launch_advanced_help.html")


class SetAdvanced(workflows.Step):
    action_class = SetAdvancedAction
    contributes = ("disk_config", "config_drive",)

    def prepare_action_context(self, request, context):
        context = super().prepare_action_context(request, context)
        # Add the workflow slug to the context so that we can tell which
        # workflow is being used when creating the action. This step is
        # used by both the Launch Instance and Resize Instance workflows.
        context['workflow_slug'] = self.workflow.slug
        return context


class SetFlavorChoiceAction(workflows.Action):
    old_flavor_id = forms.CharField(required=False, widget=forms.HiddenInput())
    old_flavor_name = forms.CharField(
        label=_("Old Flavor"),
        widget=forms.TextInput(attrs={'readonly': 'readonly'}),
        required=False,
    )
    flavor = forms.ThemableChoiceField(
        label=_("New Flavor"),
        help_text=_("Choose the flavor to launch."))

    class Meta(object):
        name = _("Flavor Choice")
        slug = 'flavor_choice'
        help_text_template = ("project/instances/"
                              "_flavors_and_quotas.html")

    def populate_flavor_choices(self, request, context):
        old_flavor_id = context.get('old_flavor_id')
        flavors = context.get('flavors').values()

        # Remove current flavor from the list of flavor choices
        flavors = [flavor for flavor in flavors if flavor.id != old_flavor_id]

        if flavors:
            if len(flavors) > 1:
                flavors = instance_utils.sort_flavor_list(request, flavors)
            else:
                flavor = flavors[0]
                flavors = [(flavor.id, flavor.name)]
            flavors.insert(0, ("", _("Select a New Flavor")))
        else:
            flavors.insert(0, ("", _("No flavors available")))
        return flavors

    def get_help_text(self, extra_context=None):
        extra = {} if extra_context is None else dict(extra_context)
        try:
            extra['usages'] = api.nova.tenant_absolute_limits(self.request,
                                                              reserved=True)
            extra['usages_json'] = json.dumps(extra['usages'])
            flavors = json.dumps([f._info for f in
                                  instance_utils.flavor_list(self.request)])
            extra['flavors'] = flavors
            extra['resize_instance'] = True
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve quota information."))
        return super().get_help_text(extra)


class SetFlavorChoice(workflows.Step):
    action_class = SetFlavorChoiceAction
    depends_on = ("instance_id", "name")
    contributes = ("old_flavor_id", "old_flavor_name", "flavors", "flavor")


class ResizeInstance(workflows.Workflow):
    slug = "resize_instance"
    name = _("Resize Instance")
    finalize_button_name = _("Resize")
    success_message = _('Request for resizing of instance "%s" '
                        'has been submitted.')
    failure_message = _('Unable to resize instance "%s".')
    success_url = "horizon:project:instances:index"
    default_steps = (SetFlavorChoice, SetAdvanced,)

    def format_status_message(self, message):
        if "%s" in message:
            return message % self.context.get('name', 'unknown instance')
        return message

    @sensitive_variables('context')
    def handle(self, request, context):
        instance_id = context.get('instance_id', None)
        flavor = context.get('flavor', None)
        disk_config = context.get('disk_config', None)
        try:
            api.nova.server_resize(request, instance_id, flavor, disk_config)
            return True
        except Exception as e:
            self.failure_message = encoding.force_str(e)
            return False
