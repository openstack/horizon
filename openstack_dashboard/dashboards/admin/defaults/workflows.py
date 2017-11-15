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

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard.api import base
from openstack_dashboard.api import cinder
from openstack_dashboard.api import nova
from openstack_dashboard.usage import quotas

LOG = logging.getLogger(__name__)


class UpdateDefaultComputeQuotasAction(workflows.Action):
    instances = forms.IntegerField(min_value=-1, label=_("Instances"))
    cores = forms.IntegerField(min_value=-1, label=_("VCPUs"))
    ram = forms.IntegerField(min_value=-1, label=_("RAM (MB)"))
    metadata_items = forms.IntegerField(min_value=-1,
                                        label=_("Metadata Items"))
    key_pairs = forms.IntegerField(min_value=-1, label=_("Key Pairs"))
    server_groups = forms.IntegerField(min_value=-1, label=_("Server Groups"))
    server_group_members = forms.IntegerField(
        min_value=-1, label=_("Server Group Members"))
    injected_files = forms.IntegerField(min_value=-1,
                                        label=_("Injected Files"))
    injected_file_content_bytes = forms.IntegerField(
        min_value=-1,
        label=_("Injected File Content Bytes"))
    injected_file_path_bytes = forms.IntegerField(
        min_value=-1,
        label=_("Length of Injected File Path"))

    def __init__(self, request, context, *args, **kwargs):
        super(UpdateDefaultComputeQuotasAction, self).__init__(
            request, context, *args, **kwargs)
        disabled_quotas = context['disabled_quotas']
        for field in disabled_quotas:
            if field in self.fields:
                self.fields[field].required = False
                self.fields[field].widget = forms.HiddenInput()

    def handle(self, request, context):
        nova_data = {
            key: value for key, value in context.items()
            if key in quotas.NOVA_QUOTA_FIELDS
        }
        try:
            nova.default_quota_update(request, **nova_data)
            return True
        except Exception:
            exceptions.handle(request,
                              _('Unable to update default compute quotas.'))
            return False

    class Meta(object):
        name = _("Compute")
        slug = 'update_default_compute_quotas'
        help_text = _("From here you can update the default compute quotas "
                      "(max limits).")


class UpdateDefaultComputeQuotasStep(workflows.Step):
    action_class = UpdateDefaultComputeQuotasAction
    contributes = quotas.NOVA_QUOTA_FIELDS
    depends_on = ('disabled_quotas',)

    def prepare_action_context(self, request, context):
        try:
            quota_defaults = nova.default_quota_get(request,
                                                    request.user.tenant_id)
            for field in quotas.NOVA_QUOTA_FIELDS:
                context[field] = quota_defaults.get(field).limit
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve default compute quotas.'))
        return context

    def allowed(self, request):
        return base.is_service_enabled(request, 'compute')


class UpdateDefaultVolumeQuotasAction(workflows.Action):
    volumes = forms.IntegerField(min_value=-1, label=_("Volumes"))
    gigabytes = forms.IntegerField(
        min_value=-1,
        label=_("Total Size of Volumes and Snapshots (GiB)"))
    snapshots = forms.IntegerField(min_value=-1, label=_("Volume Snapshots"))

    def __init__(self, request, context, *args, **kwargs):
        super(UpdateDefaultVolumeQuotasAction, self).__init__(
            request, context, *args, **kwargs)
        disabled_quotas = context['disabled_quotas']
        for field in disabled_quotas:
            if field in self.fields:
                self.fields[field].required = False
                self.fields[field].widget = forms.HiddenInput()

    def handle(self, request, context):
        cinder_data = {
            key: value for key, value in context.items()
            if key in quotas.CINDER_QUOTA_FIELDS
        }
        try:
            cinder.default_quota_update(request, **cinder_data)
            return True
        except Exception:
            exceptions.handle(request,
                              _('Unable to update default volume quotas.'))
            return False

    class Meta(object):
        name = _("Volume")
        slug = 'update_default_volume_quotas'
        help_text = _("From here you can update the default volume quotas "
                      "(max limits).")


class UpdateDefaultVolumeQuotasStep(workflows.Step):
    action_class = UpdateDefaultVolumeQuotasAction
    contributes = quotas.CINDER_QUOTA_FIELDS
    depends_on = ('disabled_quotas',)

    def prepare_action_context(self, request, context):
        try:
            quota_defaults = cinder.default_quota_get(request,
                                                      request.user.tenant_id)
            for field in quotas.CINDER_QUOTA_FIELDS:
                context[field] = quota_defaults.get(field).limit
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve default volume quotas.'))
        return context

    def allowed(self, request):
        return cinder.is_volume_service_enabled(request)


class UpdateDefaultQuotas(workflows.Workflow):
    slug = "update_default_quotas"
    name = _("Update Default Quotas")
    finalize_button_name = _("Update Defaults")
    success_message = _('Default quotas updated.')
    failure_message = _('Unable to update default quotas.')
    success_url = "horizon:admin:defaults:index"
    default_steps = (UpdateDefaultComputeQuotasStep,
                     UpdateDefaultVolumeQuotasStep)
