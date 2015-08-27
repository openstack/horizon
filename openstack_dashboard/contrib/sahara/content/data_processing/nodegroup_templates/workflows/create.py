# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from django.utils.translation import ugettext_lazy as _

from saharaclient.api import base as api_base

from horizon import exceptions
from horizon import forms
from horizon import workflows
from openstack_dashboard.api import cinder
from openstack_dashboard.api import network
from openstack_dashboard.contrib.sahara.api import sahara as saharaclient

from openstack_dashboard.contrib.sahara.content.data_processing.utils \
    import helpers
from openstack_dashboard.contrib.sahara.content.data_processing.utils \
    import workflow_helpers
from openstack_dashboard.dashboards.project.instances \
    import utils as nova_utils
from openstack_dashboard.dashboards.project.volumes \
    import utils as cinder_utils


LOG = logging.getLogger(__name__)


class GeneralConfigAction(workflows.Action):
    nodegroup_name = forms.CharField(label=_("Template Name"))

    description = forms.CharField(label=_("Description"),
                                  required=False,
                                  widget=forms.Textarea(attrs={'rows': 4}))

    flavor = forms.ChoiceField(label=_("OpenStack Flavor"))

    availability_zone = forms.ChoiceField(
        label=_("Availability Zone"),
        help_text=_("Launch instances in this availability zone."),
        required=False,
        widget=forms.Select(attrs={"class": "availability_zone_field"})
    )

    storage = forms.ChoiceField(
        label=_("Storage location"),
        help_text=_("Choose a storage location"),
        choices=[("ephemeral_drive", "Ephemeral Drive"),
                 ("cinder_volume", "Cinder Volume")],
        widget=forms.Select(attrs={
            "class": "storage_field switchable",
            'data-slug': 'storage_loc'
        }))

    volumes_per_node = forms.IntegerField(
        label=_("Volumes per node"),
        required=False,
        initial=1,
        widget=forms.TextInput(attrs={
            "class": "volume_per_node_field switched",
            "data-switch-on": "storage_loc",
            "data-storage_loc-cinder_volume": _('Volumes per node')
        })
    )

    volumes_size = forms.IntegerField(
        label=_("Volumes size (GB)"),
        required=False,
        initial=10,
        widget=forms.TextInput(attrs={
            "class": "volume_size_field switched",
            "data-switch-on": "storage_loc",
            "data-storage_loc-cinder_volume": _('Volumes size (GB)')
        })
    )

    volume_type = forms.ChoiceField(
        label=_("Volumes type"),
        required=False,
        widget=forms.Select(attrs={
            "class": "volume_type_field switched",
            "data-switch-on": "storage_loc",
            "data-storage_loc-cinder_volume": _('Volumes type')
        })
    )

    volume_local_to_instance = forms.BooleanField(
        label=_("Volume local to instance"),
        required=False,
        help_text=_("Instance and attached volumes will be created on the "
                    "same physical host"),
        widget=forms.CheckboxInput(attrs={
            "class": "volume_local_to_instance_field switched",
            "data-switch-on": "storage_loc",
            "data-storage_loc-cinder_volume": _('Volume local to instance')
        })
    )

    volumes_availability_zone = forms.ChoiceField(
        label=_("Volumes Availability Zone"),
        help_text=_("Create volumes in this availability zone."),
        required=False,
        widget=forms.Select(attrs={
            "class": "volumes_availability_zone_field switched",
            "data-switch-on": "storage_loc",
            "data-storage_loc-cinder_volume": _('Volumes Availability Zone')
        })
    )

    hidden_configure_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_configure_field"}))

    def __init__(self, request, *args, **kwargs):
        super(GeneralConfigAction, self).__init__(request, *args, **kwargs)

        hlps = helpers.Helpers(request)

        plugin, hadoop_version = (
            workflow_helpers.get_plugin_and_hadoop_version(request))
        process_choices = []
        try:
            version_details = saharaclient.plugin_get_version_details(
                request, plugin, hadoop_version)
            for service, processes in version_details.node_processes.items():
                for process in processes:
                    process_choices.append(
                        (str(service) + ":" + str(process), process))
        except Exception:
            exceptions.handle(request,
                              _("Unable to generate process choices."))

        if not saharaclient.SAHARA_AUTO_IP_ALLOCATION_ENABLED:
            pools = network.floating_ip_pools_list(request)
            pool_choices = [(pool.id, pool.name) for pool in pools]
            pool_choices.insert(0, (None, "Do not assign floating IPs"))

            self.fields['floating_ip_pool'] = forms.ChoiceField(
                label=_("Floating IP Pool"),
                choices=pool_choices,
                required=False)

        self.fields["proxygateway"] = forms.BooleanField(
            label=_("Proxy Gateway"),
            widget=forms.CheckboxInput(),
            help_text=_("Sahara will use instances of this node group to "
                        "access other cluster instances."),
            required=False)

        self.fields["processes"] = forms.MultipleChoiceField(
            label=_("Processes"),
            widget=forms.CheckboxSelectMultiple(),
            help_text=_("Processes to be launched in node group"),
            choices=process_choices)

        self.fields["plugin_name"] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=plugin
        )
        self.fields["hadoop_version"] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=hadoop_version
        )

        node_parameters = hlps.get_general_node_group_configs(plugin,
                                                              hadoop_version)
        for param in node_parameters:
            self.fields[param.name] = workflow_helpers.build_control(param)

        if request.REQUEST.get("guide_template_type"):
            self.fields["guide_template_type"] = forms.CharField(
                required=False,
                widget=forms.HiddenInput(),
                initial=request.REQUEST.get("guide_template_type"))

        try:
            volume_types = cinder.volume_type_list(request)
        except Exception:
            exceptions.handle(request,
                              _("Unable to get volume type list."))

        self.fields['volume_type'].choices = [(None, _("No volume type"))] + \
                                             [(type.name, type.name)
                                              for type in volume_types]

    def populate_flavor_choices(self, request, context):
        flavors = nova_utils.flavor_list(request)
        if flavors:
            return nova_utils.sort_flavor_list(request, flavors)
        return []

    def populate_availability_zone_choices(self, request, context):
        # The default is None, i.e. not specifying any availability zone
        az_list = [(None, _('No availability zone specified'))]
        az_list.extend([(az.zoneName, az.zoneName)
                        for az in nova_utils.availability_zone_list(request)
                        if az.zoneState['available']])
        return az_list

    def populate_volumes_availability_zone_choices(self, request, context):
        az_list = [(None, _('No availability zone specified'))]
        az_list.extend([(az.zoneName, az.zoneName)
                        for az in cinder_utils.availability_zone_list(request)
                        if az.zoneState['available']])
        return az_list

    def get_help_text(self):
        extra = dict()
        plugin, hadoop_version = (
            workflow_helpers.get_plugin_and_hadoop_version(self.request))
        extra["plugin_name"] = plugin
        extra["hadoop_version"] = hadoop_version
        return super(GeneralConfigAction, self).get_help_text(extra)

    class Meta(object):
        name = _("Configure Node Group Template")
        help_text_template = (
            "project/data_processing.nodegroup_templates"
            "/_configure_general_help.html")


class SecurityConfigAction(workflows.Action):
    def __init__(self, request, *args, **kwargs):
        super(SecurityConfigAction, self).__init__(request, *args, **kwargs)

        self.fields["security_autogroup"] = forms.BooleanField(
            label=_("Auto Security Group"),
            widget=forms.CheckboxInput(),
            help_text=_("Create security group for this Node Group."),
            required=False,
            initial=True)

        try:
            groups = network.security_group_list(request)
        except Exception:
            exceptions.handle(request,
                              _("Unable to get security group list."))
            raise

        security_group_list = [(sg.id, sg.name) for sg in groups]
        self.fields["security_groups"] = forms.MultipleChoiceField(
            label=_("Security Groups"),
            widget=forms.CheckboxSelectMultiple(),
            help_text=_("Launch instances in these security groups."),
            choices=security_group_list,
            required=False)

    class Meta(object):
        name = _("Security")
        help_text = _("Control access to instances of the node group.")


class GeneralConfig(workflows.Step):
    action_class = GeneralConfigAction
    contributes = ("general_nodegroup_name", )

    def contribute(self, data, context):
        for k, v in data.items():
            if "hidden" in k:
                continue
            context["general_" + k] = v if v != "None" else None

        post = self.workflow.request.POST
        context['general_processes'] = post.getlist("processes")
        return context


class SecurityConfig(workflows.Step):
    action_class = SecurityConfigAction
    contributes = ("security_autogroup", "security_groups")


class ConfigureNodegroupTemplate(workflow_helpers.ServiceParametersWorkflow,
                                 workflow_helpers.StatusFormatMixin):
    slug = "configure_nodegroup_template"
    name = _("Create Node Group Template")
    finalize_button_name = _("Create")
    success_message = _("Created Node Group Template %s")
    name_property = "general_nodegroup_name"
    success_url = "horizon:project:data_processing.nodegroup_templates:index"
    default_steps = (GeneralConfig, SecurityConfig)

    def __init__(self, request, context_seed, entry_point, *args, **kwargs):
        hlps = helpers.Helpers(request)

        plugin, hadoop_version = (
            workflow_helpers.get_plugin_and_hadoop_version(request))

        general_parameters = hlps.get_general_node_group_configs(
            plugin,
            hadoop_version)
        service_parameters = hlps.get_targeted_node_group_configs(
            plugin,
            hadoop_version)

        self._populate_tabs(general_parameters, service_parameters)

        super(ConfigureNodegroupTemplate, self).__init__(request,
                                                         context_seed,
                                                         entry_point,
                                                         *args, **kwargs)

    def is_valid(self):
        missing = self.depends_on - set(self.context.keys())
        if missing:
            raise exceptions.WorkflowValidationError(
                "Unable to complete the workflow. The values %s are "
                "required but not present." % ", ".join(missing))
        checked_steps = []

        if "general_processes" in self.context:
            checked_steps = self.context["general_processes"]
        enabled_services = set([])
        for process_name in checked_steps:
            enabled_services.add(str(process_name).split(":")[0])

        steps_valid = True
        for step in self.steps:
            process_name = str(getattr(step, "process_name", None))
            if process_name not in enabled_services and \
                    not isinstance(step, GeneralConfig):
                continue
            if not step.action.is_valid():
                steps_valid = False
                step.has_errors = True
        if not steps_valid:
            return steps_valid
        return self.validate(self.context)

    def handle(self, request, context):
        try:
            processes = []
            for service_process in context["general_processes"]:
                processes.append(str(service_process).split(":")[1])

            configs_dict = (
                workflow_helpers.parse_configs_from_context(
                    context, self.defaults))

            plugin, hadoop_version = (
                workflow_helpers.get_plugin_and_hadoop_version(request))

            volumes_per_node = None
            volumes_size = None
            volumes_availability_zone = None
            volume_type = None
            volume_local_to_instance = False

            if context["general_storage"] == "cinder_volume":
                volumes_per_node = context["general_volumes_per_node"]
                volumes_size = context["general_volumes_size"]
                volumes_availability_zone = \
                    context["general_volumes_availability_zone"]
                volume_type = context["general_volume_type"]
                volume_local_to_instance = \
                    context["general_volume_local_to_instance"]

            ngt = saharaclient.nodegroup_template_create(
                request,
                name=context["general_nodegroup_name"],
                plugin_name=plugin,
                hadoop_version=hadoop_version,
                description=context["general_description"],
                flavor_id=context["general_flavor"],
                volumes_per_node=volumes_per_node,
                volumes_size=volumes_size,
                volumes_availability_zone=volumes_availability_zone,
                volume_type=volume_type,
                volume_local_to_instance=volume_local_to_instance,
                node_processes=processes,
                node_configs=configs_dict,
                floating_ip_pool=context.get("general_floating_ip_pool"),
                security_groups=context["security_groups"],
                auto_security_group=context["security_autogroup"],
                is_proxy_gateway=context["general_proxygateway"],
                availability_zone=context["general_availability_zone"])

            hlps = helpers.Helpers(request)
            if hlps.is_from_guide():
                guide_type = context["general_guide_template_type"]
                request.session[guide_type + "_name"] = (
                    context["general_nodegroup_name"])
                request.session[guide_type + "_id"] = ngt.id
                self.success_url = (
                    "horizon:project:data_processing.wizard:cluster_guide")

            return True
        except api_base.APIException as e:
            self.error_description = str(e)
            return False
        except Exception:
            exceptions.handle(request)


class SelectPluginAction(workflows.Action,
                         workflow_helpers.PluginAndVersionMixin):
    hidden_create_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_create_field"}))

    def __init__(self, request, *args, **kwargs):
        super(SelectPluginAction, self).__init__(request, *args, **kwargs)

        sahara = saharaclient.client(request)
        self._generate_plugin_version_fields(sahara)

    class Meta(object):
        name = _("Select plugin and hadoop version")
        help_text_template = ("project/data_processing.nodegroup_templates"
                              "/_create_general_help.html")


class SelectPlugin(workflows.Step):
    action_class = SelectPluginAction
    contributes = ("plugin_name", "hadoop_version")

    def contribute(self, data, context):
        context = super(SelectPlugin, self).contribute(data, context)
        context["plugin_name"] = data.get('plugin_name', None)
        context["hadoop_version"] = \
            data.get(context["plugin_name"] + "_version", None)
        return context


class CreateNodegroupTemplate(workflows.Workflow):
    slug = "create_nodegroup_template"
    name = _("Create Node Group Template")
    finalize_button_name = _("Next")
    success_message = _("Created")
    failure_message = _("Could not create")
    success_url = "horizon:project:data_processing.nodegroup_templates:index"
    default_steps = (SelectPlugin,)
