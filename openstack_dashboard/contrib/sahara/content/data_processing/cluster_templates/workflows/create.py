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

import base64
import json
import logging

from django.utils.translation import ugettext_lazy as _
from saharaclient.api import base as api_base

from horizon import exceptions
from horizon import forms
from horizon import workflows
from openstack_dashboard.contrib.sahara.api import sahara as saharaclient
from openstack_dashboard.contrib.sahara.content.data_processing. \
    utils import helpers as helpers
from openstack_dashboard.contrib.sahara.content.data_processing. \
    utils import anti_affinity as aa
import openstack_dashboard.contrib.sahara.content.data_processing. \
    utils.workflow_helpers as whelpers


LOG = logging.getLogger(__name__)


class SelectPluginAction(workflows.Action):
    hidden_create_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_create_field"}))

    def __init__(self, request, *args, **kwargs):
        super(SelectPluginAction, self).__init__(request, *args, **kwargs)

        try:
            plugins = saharaclient.plugin_list(request)
        except Exception:
            plugins = []
            exceptions.handle(request,
                              _("Unable to fetch plugin list."))
        plugin_choices = [(plugin.name, plugin.title) for plugin in plugins]

        self.fields["plugin_name"] = forms.ChoiceField(
            label=_("Plugin name"),
            choices=plugin_choices,
            widget=forms.Select(attrs={"class": "plugin_name_choice"}))

        for plugin in plugins:
            field_name = plugin.name + "_version"
            choice_field = forms.ChoiceField(
                label=_("Version"),
                choices=[(version, version) for version in plugin.versions],
                widget=forms.Select(
                    attrs={"class": "plugin_version_choice "
                                    + field_name + "_choice"})
            )
            self.fields[field_name] = choice_field

    class Meta(object):
        name = _("Select plugin and hadoop version for cluster template")
        help_text_template = ("project/data_processing.cluster_templates/"
                              "_create_general_help.html")


class SelectPlugin(workflows.Step):
    action_class = SelectPluginAction


class CreateClusterTemplate(workflows.Workflow):
    slug = "create_cluster_template"
    name = _("Create Cluster Template")
    finalize_button_name = _("Next")
    success_message = _("Created")
    failure_message = _("Could not create")
    success_url = "horizon:project:data_processing.cluster_templates:index"
    default_steps = (SelectPlugin,)


class GeneralConfigAction(workflows.Action):
    hidden_configure_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_configure_field"}))

    hidden_to_delete_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_to_delete_field"}))

    cluster_template_name = forms.CharField(label=_("Template Name"))

    description = forms.CharField(label=_("Description"),
                                  required=False,
                                  widget=forms.Textarea(attrs={'rows': 4}))

    use_autoconfig = forms.BooleanField(
        label=_("Auto-configure"),
        help_text=_("If selected, instances of a cluster will be "
                    "automatically configured during creation. Otherwise you "
                    "should manually specify configuration values"),
        required=False,
        widget=forms.CheckboxInput(),
        initial=True,
    )

    anti_affinity = aa.anti_affinity_field()

    def __init__(self, request, *args, **kwargs):
        super(GeneralConfigAction, self).__init__(request, *args, **kwargs)
        plugin, hadoop_version = whelpers.\
            get_plugin_and_hadoop_version(request)

        self.fields["plugin_name"] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=plugin
        )
        self.fields["hadoop_version"] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=hadoop_version
        )

    populate_anti_affinity_choices = aa.populate_anti_affinity_choices

    def get_help_text(self):
        extra = dict()
        plugin, hadoop_version = whelpers\
            .get_plugin_and_hadoop_version(self.request)

        extra["plugin_name"] = plugin
        extra["hadoop_version"] = hadoop_version
        return super(GeneralConfigAction, self).get_help_text(extra)

    def clean(self):
        cleaned_data = super(GeneralConfigAction, self).clean()
        if cleaned_data.get("hidden_configure_field", None) \
                == "create_nodegroup":
            self._errors = dict()
        return cleaned_data

    class Meta(object):
        name = _("Details")
        help_text_template = ("project/data_processing.cluster_templates/"
                              "_configure_general_help.html")


class GeneralConfig(workflows.Step):
    action_class = GeneralConfigAction
    contributes = ("hidden_configure_field", )

    def contribute(self, data, context):
        for k, v in data.items():
            context["general_" + k] = v

        post = self.workflow.request.POST
        context['anti_affinity_info'] = post.getlist("anti_affinity")
        return context


class ConfigureNodegroupsAction(workflows.Action):
    hidden_nodegroups_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_nodegroups_field"}))
    forms_ids = forms.CharField(
        required=False,
        widget=forms.HiddenInput())

    def __init__(self, request, *args, **kwargs):
        super(ConfigureNodegroupsAction, self). \
            __init__(request, *args, **kwargs)

        plugin = request.REQUEST.get("plugin_name")
        version = request.REQUEST.get("hadoop_version")
        if plugin and not version:
            version_name = plugin + "_version"
            version = request.REQUEST.get(version_name)

        if not plugin or not version:
            self.templates = saharaclient.nodegroup_template_find(request)
        else:
            self.templates = saharaclient.nodegroup_template_find(
                request, plugin_name=plugin, hadoop_version=version)

        deletable = request.REQUEST.get("deletable", dict())

        request_source = None
        if 'forms_ids' in request.POST:
                request_source = request.POST
        elif 'forms_ids' in request.REQUEST:
                request_source = request.REQUEST
        if request_source:
            self.groups = []
            for id in json.loads(request_source['forms_ids']):
                group_name = "group_name_" + str(id)
                template_id = "template_id_" + str(id)
                count = "count_" + str(id)
                serialized = "serialized_" + str(id)
                self.groups.append({"name": request_source[group_name],
                                    "template_id": request_source[template_id],
                                    "count": request_source[count],
                                    "id": id,
                                    "deletable": deletable.get(
                                        request_source[group_name], "true"),
                                    "serialized": request_source[serialized]})

                whelpers.build_node_group_fields(self,
                                                 group_name,
                                                 template_id,
                                                 count,
                                                 serialized)

    def clean(self):
        cleaned_data = super(ConfigureNodegroupsAction, self).clean()
        if cleaned_data.get("hidden_nodegroups_field", None) \
                == "create_nodegroup":
            self._errors = dict()
        return cleaned_data

    class Meta(object):
        name = _("Node Groups")


class ConfigureNodegroups(workflows.Step):
    action_class = ConfigureNodegroupsAction
    contributes = ("hidden_nodegroups_field", )
    template_name = ("project/data_processing.cluster_templates/"
                     "cluster_node_groups_template.html")

    def contribute(self, data, context):
        for k, v in data.items():
            context["ng_" + k] = v
        return context


class ConfigureClusterTemplate(whelpers.ServiceParametersWorkflow,
                               whelpers.StatusFormatMixin):
    slug = "configure_cluster_template"
    name = _("Create Cluster Template")
    finalize_button_name = _("Create")
    success_message = _("Created Cluster Template %s")
    name_property = "general_cluster_template_name"
    success_url = "horizon:project:data_processing.cluster_templates:index"
    default_steps = (GeneralConfig,
                     ConfigureNodegroups)

    def __init__(self, request, context_seed, entry_point, *args, **kwargs):
        ConfigureClusterTemplate._cls_registry = set([])

        hlps = helpers.Helpers(request)
        plugin, hadoop_version = whelpers.\
            get_plugin_and_hadoop_version(request)
        general_parameters = hlps.get_cluster_general_configs(
            plugin,
            hadoop_version)
        service_parameters = hlps.get_targeted_cluster_configs(
            plugin,
            hadoop_version)

        self._populate_tabs(general_parameters, service_parameters)

        super(ConfigureClusterTemplate, self).__init__(request,
                                                       context_seed,
                                                       entry_point,
                                                       *args, **kwargs)

    def is_valid(self):
        steps_valid = True
        for step in self.steps:
            if not step.action.is_valid():
                steps_valid = False
                step.has_errors = True
                errors_fields = list(step.action.errors.keys())
                step.action.errors_fields = errors_fields
        if not steps_valid:
            return steps_valid
        return self.validate(self.context)

    def handle(self, request, context):
        try:
            node_groups = []
            configs_dict = whelpers.parse_configs_from_context(context,
                                                               self.defaults)

            ids = json.loads(context['ng_forms_ids'])
            for id in ids:
                name = context['ng_group_name_' + str(id)]
                template_id = context['ng_template_id_' + str(id)]
                count = context['ng_count_' + str(id)]

                raw_ng = context.get("ng_serialized_" + str(id))

                if raw_ng and raw_ng != 'null':
                    ng = json.loads(base64.urlsafe_b64decode(str(raw_ng)))
                else:
                    ng = dict()
                ng["name"] = name
                ng["count"] = count
                if template_id and template_id != u'None':
                    ng["node_group_template_id"] = template_id
                node_groups.append(ng)

            plugin, hadoop_version = whelpers.\
                get_plugin_and_hadoop_version(request)

            # TODO(nkonovalov): Fix client to support default_image_id
            saharaclient.cluster_template_create(
                request,
                context["general_cluster_template_name"],
                plugin,
                hadoop_version,
                context["general_description"],
                configs_dict,
                node_groups,
                context["anti_affinity_info"],
                use_autoconfig=context['general_use_autoconfig']
            )

            hlps = helpers.Helpers(request)
            if hlps.is_from_guide():
                request.session["guide_cluster_template_name"] = (
                    context["general_cluster_template_name"])
                self.success_url = (
                    "horizon:project:data_processing.wizard:cluster_guide")
            return True
        except api_base.APIException as e:
            self.error_description = str(e)
            return False
        except Exception:
            exceptions.handle(request,
                              _("Cluster template creation failed"))
            return False
