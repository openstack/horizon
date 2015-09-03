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

import json
import logging

from django.utils.translation import ugettext_lazy as _
import six

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard.contrib.sahara.api import sahara as saharaclient
import openstack_dashboard.contrib.sahara.content.data_processing. \
    cluster_templates.workflows.create as t_flows
import openstack_dashboard.contrib.sahara.content.data_processing. \
    clusters.workflows.create as c_flow
import openstack_dashboard.contrib.sahara.content.data_processing. \
    utils.workflow_helpers as whelpers


LOG = logging.getLogger(__name__)

DATA_SOURCE_CREATE_URL = ("horizon:project:data_processing.data_sources"
                          ":create-data-source")


class JobExecutionGeneralConfigAction(workflows.Action):
    job_input = forms.DynamicChoiceField(
        label=_("Input"),
        initial=(None, "None"),
        add_item_link=DATA_SOURCE_CREATE_URL,
        required=False)

    job_output = forms.DynamicChoiceField(
        label=_("Output"),
        initial=(None, "None"),
        add_item_link=DATA_SOURCE_CREATE_URL,
        required=False)

    def __init__(self, request, *args, **kwargs):
        super(JobExecutionGeneralConfigAction, self).__init__(request,
                                                              *args,
                                                              **kwargs)

        if request.REQUEST.get("job_id", None) is None:
            self.fields["job"] = forms.ChoiceField(
                label=_("Job"))
            self.fields["job"].choices = self.populate_job_choices(request)
        else:
            self.fields["job"] = forms.CharField(
                widget=forms.HiddenInput(),
                initial=request.REQUEST.get("job_id", None))

    def populate_job_input_choices(self, request, context):
        return self.get_data_source_choices(request, context)

    def populate_job_output_choices(self, request, context):
        return self.get_data_source_choices(request, context)

    def get_data_source_choices(self, request, context):
        try:
            data_sources = saharaclient.data_source_list(request)
        except Exception:
            data_sources = []
            exceptions.handle(request,
                              _("Unable to fetch data sources."))

        choices = [(data_source.id, data_source.name)
                   for data_source in data_sources]
        choices.insert(0, (None, 'None'))

        return choices

    def populate_job_choices(self, request):
        try:
            jobs = saharaclient.job_list(request)
        except Exception:
            jobs = []
            exceptions.handle(request,
                              _("Unable to fetch jobs."))

        choices = [(job.id, job.name)
                   for job in jobs]

        return choices

    class Meta(object):
        name = _("Job")
        help_text_template = (
            "project/data_processing.jobs/_launch_job_help.html")


class JobExecutionExistingGeneralConfigAction(JobExecutionGeneralConfigAction):
    cluster = forms.ChoiceField(
        label=_("Cluster"),
        initial=(None, "None"),
        widget=forms.Select(attrs={"class": "cluster_choice"}))

    def populate_cluster_choices(self, request, context):
        try:
            clusters = saharaclient.cluster_list(request)
        except Exception:
            clusters = []
            exceptions.handle(request,
                              _("Unable to fetch clusters."))

        choices = [(cluster.id, cluster.name)
                   for cluster in clusters]

        return choices

    class Meta(object):
        name = _("Job")
        help_text_template = (
            "project/data_processing.jobs/_launch_job_help.html")


class JobConfigAction(workflows.Action):
    MAIN_CLASS = "edp.java.main_class"
    JAVA_OPTS = "edp.java.java_opts"
    EDP_MAPPER = "edp.streaming.mapper"
    EDP_REDUCER = "edp.streaming.reducer"
    EDP_PREFIX = "edp."
    EDP_HBASE_COMMON_LIB = "edp.hbase_common_lib"
    EDP_ADAPT_FOR_OOZIE = "edp.java.adapt_for_oozie"

    property_name = forms.ChoiceField(
        required=False,
    )

    job_configs = forms.CharField(
        required=False,
        widget=forms.HiddenInput())

    job_params = forms.CharField(
        required=False,
        widget=forms.HiddenInput())

    job_args_array = forms.CharField(
        required=False,
        widget=forms.HiddenInput())

    job_type = forms.CharField(
        required=False,
        widget=forms.HiddenInput())

    main_class = forms.CharField(label=_("Main Class"),
                                 required=False)

    java_opts = forms.CharField(label=_("Java Opts"),
                                required=False)

    streaming_mapper = forms.CharField(label=_("Mapper"))

    streaming_reducer = forms.CharField(label=_("Reducer"))

    hbase_common_lib = forms.BooleanField(
        label=_("Use HBase Common library"),
        help_text=_("Run HBase EDP Jobs with common HBase library on HDFS"),
        required=False, initial=True)

    adapt_oozie = forms.BooleanField(
        label=_("Adapt For Oozie"),
        help_text=_("Automatically modify the Hadoop configuration"
                    " so that job config values are set and so that"
                    " Oozie will handle exit codes correctly."),
        required=False, initial=True)

    def __init__(self, request, *args, **kwargs):
        super(JobConfigAction, self).__init__(request, *args, **kwargs)
        job_ex_id = request.REQUEST.get("job_execution_id")
        if job_ex_id is not None:
            job_ex_id = request.REQUEST.get("job_execution_id")
            job_ex = saharaclient.job_execution_get(request, job_ex_id)
            job_configs = job_ex.job_configs
            edp_configs = {}

            if 'configs' in job_configs:
                configs, edp_configs = (
                    self.clean_edp_configs(job_configs['configs']))
                self.fields['job_configs'].initial = (
                    json.dumps(configs))

            if 'params' in job_configs:
                self.fields['job_params'].initial = (
                    json.dumps(job_configs['params']))

            if 'args' in job_configs:
                self.fields['job_args_array'].initial = (
                    json.dumps(job_configs['args']))

            if self.MAIN_CLASS in edp_configs:
                self.fields['main_class'].initial = (
                    edp_configs[self.MAIN_CLASS])
            if self.JAVA_OPTS in edp_configs:
                self.fields['java_opts'].initial = (
                    edp_configs[self.JAVA_OPTS])

            if self.EDP_MAPPER in edp_configs:
                self.fields['streaming_mapper'].initial = (
                    edp_configs[self.EDP_MAPPER])
            if self.EDP_REDUCER in edp_configs:
                self.fields['streaming_reducer'].initial = (
                    edp_configs[self.EDP_REDUCER])
            if self.EDP_HBASE_COMMON_LIB in edp_configs:
                self.fields['hbase_common_lib'].initial = (
                    edp_configs[self.EDP_HBASE_COMMON_LIB])
            if self.EDP_ADAPT_FOR_OOZIE in edp_configs:
                self.fields['adapt_oozie'].initial = (
                    edp_configs[self.EDP_ADAPT_FOR_OOZIE])

    def clean(self):
        cleaned_data = super(workflows.Action, self).clean()
        job_type = cleaned_data.get("job_type", None)

        if job_type != "MapReduce.Streaming":
            if "streaming_mapper" in self._errors:
                del self._errors["streaming_mapper"]
            if "streaming_reducer" in self._errors:
                del self._errors["streaming_reducer"]

        return cleaned_data

    def populate_property_name_choices(self, request, context):
        job_id = request.REQUEST.get("job_id") or request.REQUEST.get("job")
        job_type = saharaclient.job_get(request, job_id).type
        job_configs = (
            saharaclient.job_get_configs(request, job_type).job_config)
        choices = [(param['value'], param['name'])
                   for param in job_configs['configs']]
        return choices

    def clean_edp_configs(self, configs):
        edp_configs = {}
        for key, value in six.iteritems(configs):
            if key.startswith(self.EDP_PREFIX):
                edp_configs[key] = value
        for rmkey in edp_configs.keys():
            # remove all configs handled via other controls
            # so they do not show up in the free entry inputs
            if rmkey in [self.EDP_HBASE_COMMON_LIB,
                         self.EDP_MAPPER,
                         self.EDP_REDUCER,
                         self.MAIN_CLASS,
                         self.JAVA_OPTS,
                         self.EDP_ADAPT_FOR_OOZIE, ]:
                del configs[rmkey]
        return (configs, edp_configs)

    class Meta(object):
        name = _("Configure")
        help_text_template = (
            "project/data_processing.jobs/_launch_job_configure_help.html")


class JobExecutionGeneralConfig(workflows.Step):
    action_class = JobExecutionGeneralConfigAction

    def contribute(self, data, context):
        for k, v in data.items():
            if k in ["job_input", "job_output"]:
                context["job_general_" + k] = None if (v in [None, ""]) else v
            else:
                context["job_general_" + k] = v

        return context


class JobExecutionExistingGeneralConfig(workflows.Step):
    action_class = JobExecutionExistingGeneralConfigAction

    def contribute(self, data, context):
        for k, v in data.items():
            if k in ["job_input", "job_output"]:
                context["job_general_" + k] = None if (v in [None, ""]) else v
            else:
                context["job_general_" + k] = v

        return context


class JobConfig(workflows.Step):
    action_class = JobConfigAction
    template_name = 'project/data_processing.jobs/config_template.html'

    def contribute(self, data, context):
        job_config = self.clean_configs(
            json.loads(data.get("job_configs", '{}')))
        job_params = self.clean_configs(
            json.loads(data.get("job_params", '{}')))
        job_args_array = self.clean_configs(
            json.loads(data.get("job_args_array", '[]')))
        job_type = data.get("job_type", '')

        context["job_type"] = job_type
        context["job_config"] = {"configs": job_config}
        context["job_config"]["args"] = job_args_array

        if job_type in ["Java", "Spark", "Storm"]:
            context["job_config"]["configs"][JobConfigAction.MAIN_CLASS] = (
                data.get("main_class", ""))
            context["job_config"]["configs"][JobConfigAction.JAVA_OPTS] = (
                data.get("java_opts", ""))
            context["job_config"]["configs"][
                JobConfigAction.EDP_HBASE_COMMON_LIB] = (
                    data.get("hbase_common_lib", True))
            if job_type == "Java":
                context["job_config"]["configs"][
                    JobConfigAction.EDP_ADAPT_FOR_OOZIE] = (
                        data.get("adapt_oozie", True))
        elif job_type == "MapReduce.Streaming":
            context["job_config"]["configs"][JobConfigAction.EDP_MAPPER] = (
                data.get("streaming_mapper", ""))
            context["job_config"]["configs"][JobConfigAction.EDP_REDUCER] = (
                data.get("streaming_reducer", ""))
        else:
            context["job_config"]["params"] = job_params

        return context

    @staticmethod
    def clean_configs(configs):
        cleaned_conf = None
        if isinstance(configs, dict):
            cleaned_conf = dict([(k.strip(), v.strip())
                                 for k, v in configs.items()
                                 if len(v.strip()) > 0 and len(k.strip()) > 0])
        elif isinstance(configs, list):
            cleaned_conf = list([v.strip() for v in configs
                                 if len(v.strip()) > 0])
        return cleaned_conf


class NewClusterConfigAction(c_flow.GeneralConfigAction):
    persist_cluster = forms.BooleanField(
        label=_("Persist cluster after job exit"),
        required=False)

    class Meta(object):
        name = _("Configure Cluster")
        help_text_template = (
            "project/data_processing.clusters/_configure_general_help.html")


class ClusterGeneralConfig(workflows.Step):
    action_class = NewClusterConfigAction
    contributes = ("hidden_configure_field", )

    def contribute(self, data, context):
        for k, v in data.items():
            context["cluster_general_" + k] = v

        return context


class LaunchJob(workflows.Workflow):
    slug = "launch_job"
    name = _("Launch Job")
    finalize_button_name = _("Launch")
    success_message = _("Job launched")
    failure_message = _("Could not launch job")
    success_url = "horizon:project:data_processing.job_executions:index"
    default_steps = (JobExecutionExistingGeneralConfig, JobConfig)

    def handle(self, request, context):
        saharaclient.job_execution_create(
            request,
            context["job_general_job"],
            context["job_general_cluster"],
            context["job_general_job_input"],
            context["job_general_job_output"],
            context["job_config"])
        return True


class SelectHadoopPluginAction(t_flows.SelectPluginAction):
    def __init__(self, request, *args, **kwargs):
        super(SelectHadoopPluginAction, self).__init__(request,
                                                       *args,
                                                       **kwargs)
        self.fields["job_id"] = forms.ChoiceField(
            label=_("Plugin name"),
            initial=request.GET.get("job_id") or request.POST.get("job_id"),
            widget=forms.HiddenInput(attrs={"class": "hidden_create_field"}))

        self.fields["job_configs"] = forms.ChoiceField(
            label=_("Job configs"),
            widget=forms.HiddenInput(attrs={"class": "hidden_create_field"}))

        self.fields["job_args"] = forms.ChoiceField(
            label=_("Job args"),
            widget=forms.HiddenInput(attrs={"class": "hidden_create_field"}))

        self.fields["job_params"] = forms.ChoiceField(
            label=_("Job params"),
            widget=forms.HiddenInput(attrs={"class": "hidden_create_field"}))

        job_ex_id = request.REQUEST.get("job_execution_id")
        if job_ex_id is not None:
            self.fields["job_execution_id"] = forms.ChoiceField(
                label=_("Job Execution ID"),
                initial=request.REQUEST.get("job_execution_id"),
                widget=forms.HiddenInput(
                    attrs={"class": "hidden_create_field"}))

            job_ex_id = request.REQUEST.get("job_execution_id")
            job_configs = (
                saharaclient.job_execution_get(request,
                                               job_ex_id).job_configs)

            if "configs" in job_configs:
                self.fields["job_configs"].initial = (
                    json.dumps(job_configs["configs"]))
            if "params" in job_configs:
                self.fields["job_params"].initial = (
                    json.dumps(job_configs["params"]))
            if "args" in job_configs:
                self.fields["job_args"].initial = (
                    json.dumps(job_configs["args"]))

    class Meta(object):
        name = _("Select plugin and hadoop version for cluster")
        help_text_template = ("project/data_processing.clusters/"
                              "_create_general_help.html")


class SelectHadoopPlugin(workflows.Step):
    action_class = SelectHadoopPluginAction


class ChosePluginVersion(workflows.Workflow):
    slug = "lunch_job"
    name = _("Launch Job")
    finalize_button_name = _("Create")
    success_message = _("Created")
    failure_message = _("Could not create")
    success_url = "horizon:project:data_processing.cluster_templates:index"
    default_steps = (SelectHadoopPlugin,)


class LaunchJobNewCluster(workflows.Workflow):
    slug = "launch_job"
    name = _("Launch Job")
    finalize_button_name = _("Launch")
    success_message = _("Job launched")
    failure_message = _("Could not launch job")
    success_url = "horizon:project:data_processing.jobs:index"
    default_steps = (ClusterGeneralConfig,
                     JobExecutionGeneralConfig,
                     JobConfig)

    def handle(self, request, context):
        node_groups = None

        plugin, hadoop_version = (
            whelpers.get_plugin_and_hadoop_version(request))

        ct_id = context["cluster_general_cluster_template"] or None
        user_keypair = context["cluster_general_keypair"] or None

        try:
            cluster = saharaclient.cluster_create(
                request,
                context["cluster_general_cluster_name"],
                plugin, hadoop_version,
                cluster_template_id=ct_id,
                default_image_id=context["cluster_general_image"],
                description=context["cluster_general_description"],
                node_groups=node_groups,
                user_keypair_id=user_keypair,
                is_transient=not(context["cluster_general_persist_cluster"]),
                net_id=context.get(
                    "cluster_general_neutron_management_network",
                    None))
        except Exception:
            exceptions.handle(request,
                              _("Unable to create new cluster for job."))
            return False

        try:
            saharaclient.job_execution_create(
                request,
                context["job_general_job"],
                cluster.id,
                context["job_general_job_input"],
                context["job_general_job_output"],
                context["job_config"])
        except Exception:
            exceptions.handle(request,
                              _("Unable to launch job."))
            return False
        return True
