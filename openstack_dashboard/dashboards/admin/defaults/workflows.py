# Copyright 2013 Kylin, Inc.
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


from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard.api import base
from openstack_dashboard.api import cinder
from openstack_dashboard.api import nova
from openstack_dashboard.usage import quotas

ALL_NOVA_QUOTA_FIELDS = quotas.NOVA_QUOTA_FIELDS + quotas.MISSING_QUOTA_FIELDS


class UpdateDefaultQuotasAction(workflows.Action):
    ifcb_label = _("Injected File Content Bytes")
    ifpb_label = _("Length of Injected File Path")
    injected_file_content_bytes = forms.IntegerField(min_value=-1,
                                                     label=ifcb_label)
    metadata_items = forms.IntegerField(min_value=-1,
                                        label=_("Metadata Items"))
    ram = forms.IntegerField(min_value=-1, label=_("RAM (MB)"))
    floating_ips = forms.IntegerField(min_value=-1, label=_("Floating IPs"))
    key_pairs = forms.IntegerField(min_value=-1, label=_("Key Pairs"))
    injected_file_path_bytes = forms.IntegerField(min_value=-1,
                                                  label=ifpb_label)
    instances = forms.IntegerField(min_value=-1, label=_("Instances"))
    security_group_rules = forms.IntegerField(min_value=-1,
                                              label=_("Security Group Rules"))
    injected_files = forms.IntegerField(min_value=-1,
                                        label=_("Injected Files"))
    cores = forms.IntegerField(min_value=-1, label=_("VCPUs"))
    security_groups = forms.IntegerField(min_value=-1,
                                         label=_("Security Groups"))
    gigabytes = forms.IntegerField(
        min_value=-1,
        label=_("Total Size of Volumes and Snapshots (GB)"))
    snapshots = forms.IntegerField(min_value=-1, label=_("Volume Snapshots"))
    volumes = forms.IntegerField(min_value=-1, label=_("Volumes"))

    def __init__(self, request, *args, **kwargs):
        super(UpdateDefaultQuotasAction, self).__init__(request,
                                                        *args,
                                                        **kwargs)
        disabled_quotas = quotas.get_disabled_quotas(request)
        for field in disabled_quotas:
            if field in self.fields:
                self.fields[field].required = False
                self.fields[field].widget = forms.HiddenInput()

    class Meta(object):
        name = _("Default Quotas")
        slug = 'update_default_quotas'
        help_text = _("From here you can update the default quotas "
                      "(max limits).")


class UpdateDefaultQuotasStep(workflows.Step):
    action_class = UpdateDefaultQuotasAction
    contributes = (quotas.QUOTA_FIELDS + quotas.MISSING_QUOTA_FIELDS)


class UpdateDefaultQuotas(workflows.Workflow):
    slug = "update_default_quotas"
    name = _("Update Default Quotas")
    finalize_button_name = _("Update Defaults")
    success_message = _('Default quotas updated.')
    failure_message = _('Unable to update default quotas.')
    success_url = "horizon:admin:defaults:index"
    default_steps = (UpdateDefaultQuotasStep,)

    def handle(self, request, data):
        # Update the default quotas.
        # `fixed_ips` update for quota class is not supported by novaclient
        nova_data = dict([(key, data[key]) for key in ALL_NOVA_QUOTA_FIELDS
                         if key != 'fixed_ips'])
        try:
            nova.default_quota_update(request, **nova_data)

            if base.is_service_enabled(request, 'volume'):
                cinder_data = dict([(key, data[key]) for key in
                                    quotas.CINDER_QUOTA_FIELDS])
                cinder.default_quota_update(request, **cinder_data)
        except Exception:
            exceptions.handle(request, _('Unable to update default quotas.'))
        return True
