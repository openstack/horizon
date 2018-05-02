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


from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks.ports import sg_base
from openstack_dashboard.utils import filters

INDEX_URL = "horizon:projects:instances:index"
ADD_USER_URL = "horizon:projects:instances:create_user"
INSTANCE_SEC_GROUP_SLUG = "update_security_groups"


class UpdateInstanceSecurityGroupsAction(sg_base.BaseSecurityGroupsAction):
    def _get_initial_security_groups(self, context):
        instance_id = context.get('instance_id', '')
        sec_groups = api.neutron.server_security_groups(self.request,
                                                        instance_id)
        return [group.id for group in sec_groups]

    def handle(self, request, data):
        instance_id = data['instance_id']
        wanted_groups = [filters.get_int_or_uuid(sg)
                         for sg in data['wanted_groups']]
        try:
            api.neutron.server_update_security_groups(request, instance_id,
                                                      wanted_groups)
        except Exception as e:
            exceptions.handle(request, str(e))
            return False
        return True

    class Meta(object):
        name = _("Security Groups")
        slug = INSTANCE_SEC_GROUP_SLUG
        help_text_template = 'project/instances/_edit_security_group_help.html'


class UpdateInstanceSecurityGroups(sg_base.BaseSecurityGroups):
    action_class = UpdateInstanceSecurityGroupsAction
    members_list_title = _("Instance Security Groups")
    depends_on = ("instance_id", "target_tenant_id")

    def allowed(self, request):
        return api.base.is_service_enabled(request, 'network')


class UpdateInstanceInfoAction(workflows.Action):
    name = forms.CharField(label=_("Name"),
                           max_length=255)
    description = forms.CharField(
        label=_("Description"),
        widget=forms.Textarea(attrs={'rows': 4}),
        max_length=255,
        required=False
    )

    def __init__(self, request, *args, **kwargs):
        super(UpdateInstanceInfoAction, self).__init__(request,
                                                       *args,
                                                       **kwargs)
        if not api.nova.is_feature_available(request, "instance_description"):
            del self.fields["description"]

    def handle(self, request, data):
        try:
            api.nova.server_update(request,
                                   data['instance_id'],
                                   data['name'],
                                   description=data.get('description'))
        except Exception:
            exceptions.handle(request, ignore=True)
            return False
        return True

    class Meta(object):
        name = _("Information")
        slug = 'instance_info'
        help_text = _("Edit the instance details.")


class UpdateInstanceInfo(workflows.Step):
    action_class = UpdateInstanceInfoAction
    depends_on = ("instance_id",)
    contributes = ("name", "description")


class UpdateInstance(workflows.Workflow):
    slug = "update_instance"
    name = _("Edit Instance")
    finalize_button_name = _("Save")
    success_message = _('Modified instance "%s".')
    failure_message = _('Unable to modify instance "%s".')
    success_url = "horizon:project:instances:index"
    default_steps = (UpdateInstanceInfo,
                     UpdateInstanceSecurityGroups)

    def format_status_message(self, message):
        return message % self.context.get('name', 'unknown instance')


# NOTE(kspear): nova doesn't support instance security group management
#               by an admin. This isn't really the place for this code,
#               but the other ways of special-casing this are even messier.
class AdminUpdateInstance(UpdateInstance):
    success_url = "horizon:admin:instances:index"
    default_steps = (UpdateInstanceInfo,)
