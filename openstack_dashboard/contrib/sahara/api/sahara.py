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

from django.conf import settings

from horizon import exceptions
from horizon.utils.memoized import memoized  # noqa
from openstack_dashboard.api import base

from saharaclient.api.base import APIException
from saharaclient import client as api_client


LOG = logging.getLogger(__name__)

# "type" of Sahara service registered in keystone
SAHARA_SERVICE = 'data-processing'
# Sahara service_type registered in Juno
SAHARA_SERVICE_FALLBACK = 'data_processing'

SAHARA_AUTO_IP_ALLOCATION_ENABLED = getattr(
    settings,
    'SAHARA_AUTO_IP_ALLOCATION_ENABLED',
    False)
VERSIONS = base.APIVersionManager(
    SAHARA_SERVICE,
    preferred_version=getattr(settings,
                              'OPENSTACK_API_VERSIONS',
                              {}).get(SAHARA_SERVICE, 1.1))
VERSIONS.load_supported_version(1.1, {"client": api_client,
                                      "version": 1.1})


def safe_call(func, *args, **kwargs):
    """Call a function ignoring Not Found error

    This method is supposed to be used only for safe retrieving Sahara
    objects. If the object is no longer available the None should be
    returned.

    """

    try:
        return func(*args, **kwargs)
    except APIException as e:
        if e.error_code == 404:
            return None  # Not found. Exiting with None
        raise  # Other errors are not expected here


@memoized
def client(request):
    try:
        service_type = SAHARA_SERVICE
        sahara_url = base.url_for(request, service_type)
    except exceptions.ServiceCatalogException:
        # if no endpoint found, fallback to the old service_type
        service_type = SAHARA_SERVICE_FALLBACK
        sahara_url = base.url_for(request, service_type)

    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    return api_client.Client(VERSIONS.get_active_version()["version"],
                             sahara_url=sahara_url,
                             service_type=service_type,
                             project_id=request.user.project_id,
                             input_auth_token=request.user.token.id,
                             insecure=insecure,
                             cacert=cacert)


def image_list(request, search_opts=None):
    return client(request).images.list(search_opts=search_opts)


def image_get(request, image_id):
    return client(request).images.get(id=image_id)


def image_unregister(request, image_id):
    client(request).images.unregister_image(image_id=image_id)


def image_update(request, image_id, user_name, desc):
    client(request).images.update_image(image_id=image_id,
                                        user_name=user_name,
                                        desc=desc)


def image_tags_update(request, image_id, image_tags):
    client(request).images.update_tags(image_id=image_id,
                                       new_tags=image_tags)


def plugin_list(request, search_opts=None):
    return client(request).plugins.list(search_opts=search_opts)


def plugin_get(request, plugin_name):
    return client(request).plugins.get(plugin_name=plugin_name)


def plugin_get_version_details(request, plugin_name, hadoop_version):
    return client(request).plugins.get_version_details(
        plugin_name=plugin_name,
        hadoop_version=hadoop_version)


def plugin_convert_to_template(request, plugin_name, hadoop_version,
                               template_name, file_content):
    return client(request).plugins.convert_to_cluster_template(
        plugin_name=plugin_name,
        hadoop_version=hadoop_version,
        template_name=template_name,
        filecontent=file_content)


def nodegroup_template_create(request, name, plugin_name, hadoop_version,
                              flavor_id, description=None,
                              volumes_per_node=None, volumes_size=None,
                              node_processes=None, node_configs=None,
                              floating_ip_pool=None, security_groups=None,
                              auto_security_group=False,
                              availability_zone=False,
                              volumes_availability_zone=False,
                              volume_type=None,
                              is_proxy_gateway=False,
                              volume_local_to_instance=False,
                              use_autoconfig=None):
    return client(request).node_group_templates.create(
        name=name,
        plugin_name=plugin_name,
        hadoop_version=hadoop_version,
        flavor_id=flavor_id,
        description=description,
        volumes_per_node=volumes_per_node,
        volumes_size=volumes_size,
        node_processes=node_processes,
        node_configs=node_configs,
        floating_ip_pool=floating_ip_pool,
        security_groups=security_groups,
        auto_security_group=auto_security_group,
        availability_zone=availability_zone,
        volumes_availability_zone=volumes_availability_zone,
        volume_type=volume_type,
        is_proxy_gateway=is_proxy_gateway,
        volume_local_to_instance=volume_local_to_instance,
        use_autoconfig=use_autoconfig)


def nodegroup_template_list(request, search_opts=None):
    return client(request).node_group_templates.list(search_opts=search_opts)


def nodegroup_template_get(request, ngt_id):
    return client(request).node_group_templates.get(ng_template_id=ngt_id)


def nodegroup_template_find(request, **kwargs):
    return client(request).node_group_templates.find(**kwargs)


def nodegroup_template_delete(request, ngt_id):
    client(request).node_group_templates.delete(ng_template_id=ngt_id)


def nodegroup_template_update(request, ngt_id, name, plugin_name,
                              hadoop_version, flavor_id,
                              description=None, volumes_per_node=None,
                              volumes_size=None, node_processes=None,
                              node_configs=None, floating_ip_pool=None,
                              security_groups=None, auto_security_group=False,
                              availability_zone=False,
                              volumes_availability_zone=False,
                              volume_type=None,
                              is_proxy_gateway=False,
                              volume_local_to_instance=False,
                              use_autoconfig=None):
    return client(request).node_group_templates.update(
        ng_template_id=ngt_id,
        name=name,
        plugin_name=plugin_name,
        hadoop_version=hadoop_version,
        flavor_id=flavor_id,
        description=description,
        volumes_per_node=volumes_per_node,
        volumes_size=volumes_size,
        node_processes=node_processes,
        node_configs=node_configs,
        floating_ip_pool=floating_ip_pool,
        security_groups=security_groups,
        auto_security_group=auto_security_group,
        availability_zone=availability_zone,
        volumes_availability_zone=volumes_availability_zone,
        volume_type=volume_type,
        is_proxy_gateway=is_proxy_gateway,
        volume_local_to_instance=volume_local_to_instance,
        use_autoconfig=use_autoconfig)


def cluster_template_create(request, name, plugin_name, hadoop_version,
                            description=None, cluster_configs=None,
                            node_groups=None, anti_affinity=None,
                            net_id=None, use_autoconfig=None):
    return client(request).cluster_templates.create(
        name=name,
        plugin_name=plugin_name,
        hadoop_version=hadoop_version,
        description=description,
        cluster_configs=cluster_configs,
        node_groups=node_groups,
        anti_affinity=anti_affinity,
        net_id=net_id,
        use_autoconfig=use_autoconfig)


def cluster_template_list(request, search_opts=None):
    return client(request).cluster_templates.list(search_opts=search_opts)


def cluster_template_get(request, ct_id):
    return client(request).cluster_templates.get(cluster_template_id=ct_id)


def cluster_template_delete(request, ct_id):
    client(request).cluster_templates.delete(cluster_template_id=ct_id)


def cluster_template_update(request, ct_id, name, plugin_name,
                            hadoop_version, description=None,
                            cluster_configs=None, node_groups=None,
                            anti_affinity=None, net_id=None,
                            use_autoconfig=None):
    try:
        template = client(request).cluster_templates.update(
            cluster_template_id=ct_id,
            name=name,
            plugin_name=plugin_name,
            hadoop_version=hadoop_version,
            description=description,
            cluster_configs=cluster_configs,
            node_groups=node_groups,
            anti_affinity=anti_affinity,
            net_id=net_id,
            use_autoconfig=use_autoconfig)

    except APIException as e:
        raise exceptions.Conflict(e)
    return template


def cluster_create(request, name, plugin_name, hadoop_version,
                   cluster_template_id=None, default_image_id=None,
                   is_transient=None, description=None, cluster_configs=None,
                   node_groups=None, user_keypair_id=None,
                   anti_affinity=None, net_id=None, use_autoconfig=None):
    return client(request).clusters.create(
        name=name,
        plugin_name=plugin_name,
        hadoop_version=hadoop_version,
        cluster_template_id=cluster_template_id,
        default_image_id=default_image_id,
        is_transient=is_transient,
        description=description,
        cluster_configs=cluster_configs,
        node_groups=node_groups,
        user_keypair_id=user_keypair_id,
        anti_affinity=anti_affinity,
        net_id=net_id,
        use_autoconfig=use_autoconfig)


def cluster_scale(request, cluster_id, scale_object):
    return client(request).clusters.scale(
        cluster_id=cluster_id,
        scale_object=scale_object)


def cluster_list(request, search_opts=None):
    return client(request).clusters.list(search_opts=search_opts)


def cluster_get(request, cluster_id, show_progress=False):
    return client(request).clusters.get(
        cluster_id=cluster_id,
        show_progress=show_progress)


def cluster_delete(request, cluster_id):
    client(request).clusters.delete(cluster_id=cluster_id)


def data_source_create(request, name, description, ds_type, url,
                       credential_user=None, credential_pass=None):
    return client(request).data_sources.create(
        name=name,
        description=description,
        data_source_type=ds_type,
        url=url,
        credential_user=credential_user,
        credential_pass=credential_pass)


def data_source_list(request, search_opts=None):
    return client(request).data_sources.list(search_opts=search_opts)


def data_source_get(request, ds_id):
    return client(request).data_sources.get(data_source_id=ds_id)


def data_source_delete(request, ds_id):
    client(request).data_sources.delete(data_source_id=ds_id)


def data_source_update(request, ds_id, data):
    return client(request).data_sources.update(ds_id, data)


def job_binary_create(request, name, url, description, extra):
    return client(request).job_binaries.create(
        name=name,
        url=url,
        description=description,
        extra=extra)


def job_binary_list(request, search_opts=None):
    return client(request).job_binaries.list(search_opts=search_opts)


def job_binary_get(request, jb_id):
    return client(request).job_binaries.get(job_binary_id=jb_id)


def job_binary_delete(request, jb_id):
    client(request).job_binaries.delete(job_binary_id=jb_id)


def job_binary_get_file(request, jb_id):
    return client(request).job_binaries.get_file(job_binary_id=jb_id)


def job_binary_update(request, jb_id, data):
    return client(request).job_binaries.update(jb_id, data)


def job_binary_internal_create(request, name, data):
    return client(request).job_binary_internals.create(
        name=name,
        data=data)


def job_binary_internal_list(request, search_opts=None):
    return client(request).job_binary_internals.list(search_opts=search_opts)


def job_binary_internal_get(request, jbi_id):
    # The argument name looks wrong. This should be changed in the sahara
    # client first and then updated here
    return client(request).job_binary_internals.get(job_binary_id=jbi_id)


def job_binary_internal_delete(request, jbi_id):
    # The argument name looks wrong. This should be changed in the sahara
    # client first and then updated here
    client(request).job_binary_internals.delete(job_binary_id=jbi_id)


def job_create(request, name, j_type, mains, libs, description):
    return client(request).jobs.create(
        name=name,
        type=j_type,
        mains=mains,
        libs=libs,
        description=description)


def job_list(request, search_opts=None):
    return client(request).jobs.list(search_opts=search_opts)


def job_get(request, job_id):
    return client(request).jobs.get(job_id=job_id)


def job_delete(request, job_id):
    client(request).jobs.delete(job_id=job_id)


def job_get_configs(request, job_type):
    return client(request).jobs.get_configs(job_type=job_type)


def job_execution_create(request, job_id, cluster_id,
                         input_id, output_id, configs):
    return client(request).job_executions.create(
        job_id=job_id,
        cluster_id=cluster_id,
        input_id=input_id,
        output_id=output_id,
        configs=configs)


def _resolve_job_execution_names(job_execution, cluster=None,
                                 job=None):

    job_execution.cluster_name = None
    if cluster:
        job_execution.cluster_name = cluster.name

    job_execution.job_name = None
    if job:
        job_execution.job_name = job.name

    return job_execution


def job_execution_list(request, search_opts=None):
    job_execution_list = client(request).job_executions.list(
        search_opts=search_opts)
    job_dict = dict((j.id, j) for j in job_list(request))
    cluster_dict = dict((c.id, c) for c in cluster_list(request))

    resolved_job_execution_list = [
        _resolve_job_execution_names(
            job_execution,
            cluster_dict.get(job_execution.cluster_id),
            job_dict.get(job_execution.job_id))
        for job_execution in job_execution_list
    ]

    return resolved_job_execution_list


def job_execution_get(request, jex_id):
    jex = client(request).job_executions.get(obj_id=jex_id)
    cluster = safe_call(client(request).clusters.get, jex.cluster_id)
    job = safe_call(client(request).jobs.get, jex.job_id)

    return _resolve_job_execution_names(jex, cluster, job)


def job_execution_delete(request, jex_id):
    client(request).job_executions.delete(obj_id=jex_id)


def job_types_list(request):
    return client(request).job_types.list()
