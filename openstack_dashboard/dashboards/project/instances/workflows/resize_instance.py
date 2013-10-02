# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django.utils.translation import ugettext_lazy as _  # noqa
from django.views.decorators.debug import sensitive_variables  # noqa

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard import api


class SetFlavorChoiceAction(workflows.Action):
    old_flavor_id = forms.CharField(required=False, widget=forms.HiddenInput())
    old_flavor_name = forms.CharField(label=_("Old Flavor"),
                                 required=False,
                                 widget=forms.TextInput(
                                     attrs={'readonly': 'readonly'}
                                 ))
    flavor = forms.ChoiceField(label=_("New Flavor"),
                               required=True,
                               help_text=_("Choose the flavor to launch."))

    class Meta:
        name = _("Flavor Choice")
        slug = 'flavor_choice'
        help_text_template = ("project/instances/"
                              "_flavors_and_quotas.html")

    def clean(self):
        cleaned_data = super(SetFlavorChoiceAction, self).clean()
        flavor = cleaned_data.get('flavor', None)

        if flavor is None or flavor == cleaned_data['old_flavor_id']:
            raise forms.ValidationError(_('Please  choose a new flavor that '
                                          'can not be same as the old one.'))
        return cleaned_data

    def populate_flavor_choices(self, request, context):
        flavors = context.get('flavors')
        flavor_list = [(flavor.id, '%s' % flavor.name)
                       for flavor in flavors.values()]
        if flavor_list:
            flavor_list.insert(0, ("", _("Select an New Flavor")))
        else:
            flavor_list.insert(0, ("", _("No flavors available.")))
        return sorted(flavor_list)

    def get_help_text(self):
        extra = {}
        try:
            extra['usages'] = api.nova.tenant_absolute_limits(self.request)
            extra['usages_json'] = json.dumps(extra['usages'])
            flavors = json.dumps([f._info for f in
                                  api.nova.flavor_list(self.request)])
            extra['flavors'] = flavors
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve quota information."))
        return super(SetFlavorChoiceAction, self).get_help_text(extra)


class SetFlavorChoice(workflows.Step):
    action_class = SetFlavorChoiceAction
    depends_on = ("instance_id", "name")
    contributes = ("old_flavor_id", "old_flavor_name", "flavors", "flavor")


class ResizeInstance(workflows.Workflow):
    slug = "resize_instance"
    name = _("Resize Instance")
    finalize_button_name = _("Resize")
    success_message = _('Preparing instance "%s" for resize.')
    failure_message = _('Unable to resize instance "%s".')
    success_url = "horizon:project:instances:index"
    default_steps = (SetFlavorChoice,)

    def format_status_message(self, message):
        return message % self.context.get('name', 'unknown instance')

    @sensitive_variables('context')
    def handle(self, request, context):
        instance_id = context.get('instance_id', None)
        flavor = context.get('flavor', None)
        try:
            api.nova.server_resize(request, instance_id, flavor)
            return True
        except Exception:
            exceptions.handle(request)
            return False
