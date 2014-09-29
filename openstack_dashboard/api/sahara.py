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

from horizon.utils.memoized import memoized  # noqa
from openstack_dashboard.api import base

from saharaclient import client as api_client


LOG = logging.getLogger(__name__)


# "type" of Sahara service registered in keystone
SAHARA_SERVICE = 'data_processing'

SAHARA_AUTO_IP_ALLOCATION_ENABLED = getattr(settings,
    'SAHARA_AUTO_IP_ALLOCATION_ENABLED',
    False)
VERSIONS = base.APIVersionManager(SAHARA_SERVICE,
    preferred_version=getattr(settings,
                              'OPENSTACK_API_VERSIONS',
                              {}).get(SAHARA_SERVICE, 1.1))
VERSIONS.load_supported_version(1.1, {"client": api_client,
                                      "version": 1.1})


@memoized
def client(request):
    return api_client.Client(VERSIONS.get_active_version()["version"],
                             sahara_url=base.url_for(request, SAHARA_SERVICE),
                             service_type=SAHARA_SERVICE,
                             project_id=request.user.project_id,
                             input_auth_token=request.user.token.id)


def image_list(request):
    return client(request).images.list()


def image_get(request, image_id):
    return client(request).images.get(image_id)


def image_unregister(request, image_id):
    client(request).images.unregister_image(image_id)


def image_update(request, image_id, user_name, desc):
    client(request).images.update_image(image_id, user_name, desc)


def image_tags_update(request, image_id, image_tags):
    client(request).images.update_tags(image_id, image_tags)


def plugin_list(request):
    return client(request).plugins.list()


def plugin_get(request, plugin_name):
    return client(request).plugins.get(plugin_name)


def plugin_get_version_details(request, plugin_name, hadoop_version):
    return client(request).plugins.get_version_details(plugin_name,
                                                       hadoop_version)


def plugin_convert_to_template(request, plugin_name, hadoop_version,
                               template_name, file_content):
    return client(request).plugins.convert_to_cluster_template(plugin_name,
                                                       hadoop_version,
                                                       template_name,
                                                       file_content)


def nodegroup_template_create(request, name, plugin_name, hadoop_version,
                              flavor_id, description=None,
                              volumes_per_node=None, volumes_size=None,
                              node_processes=None, node_configs=None,
                              floating_ip_pool=None, security_groups=None,
                              auto_security_group=False):
    return client(request).node_group_templates.create(name, plugin_name,
                                                       hadoop_version,
                                                       flavor_id, description,
                                                       volumes_per_node,
                                                       volumes_size,
                                                       node_processes,
                                                       node_configs,
                                                       floating_ip_pool,
                                                       security_groups,
                                                       auto_security_group)


def nodegroup_template_list(request):
    return client(request).node_group_templates.list()


def nodegroup_template_get(request, ngt_id):
    return client(request).node_group_templates.get(ngt_id)


def nodegroup_template_find(request, **kwargs):
    return client(request).node_group_templates.find(**kwargs)


def nodegroup_template_delete(request, ngt_id):
    client(request).node_group_templates.delete(ngt_id)


def nodegroup_template_update(request, ngt_id, name, plugin_name,
                              hadoop_version, flavor_id,
                              description=None, volumes_per_node=None,
                              volumes_size=None, node_processes=None,
                              node_configs=None, floating_ip_pool=None):
    return client(request).node_group_templates.update(ngt_id, name,
                                                       plugin_name,
                                                       hadoop_version,
                                                       flavor_id,
                                                       description,
                                                       volumes_per_node,
                                                       volumes_size,
                                                       node_processes,
                                                       node_configs,
                                                       floating_ip_pool)


def cluster_template_create(request, name, plugin_name, hadoop_version,
                            description=None, cluster_configs=None,
                            node_groups=None, anti_affinity=None,
                            net_id=None):
    return client(request).cluster_templates.create(name, plugin_name,
                                                    hadoop_version,
                                                    description,
                                                    cluster_configs,
                                                    node_groups,
                                                    anti_affinity,
                                                    net_id)


def cluster_template_list(request):
    return client(request).cluster_templates.list()


def cluster_template_get(request, ct_id):
    return client(request).cluster_templates.get(ct_id)


def cluster_template_delete(request, ct_id):
    client(request).cluster_templates.delete(ct_id)


def cluster_template_update(request, ct_id, name, plugin_name,
                            hadoop_version, description=None,
                            cluster_configs=None, node_groups=None,
                            anti_affinity=None, net_id=None):
    return client(request).cluster_templates.update(ct_id, name,
                                                    plugin_name,
                                                    hadoop_version,
                                                    description,
                                                    cluster_configs,
                                                    node_groups,
                                                    anti_affinity,
                                                    net_id)


def cluster_create(request, name, plugin_name, hadoop_version,
                   cluster_template_id=None, default_image_id=None,
                   is_transient=None, description=None, cluster_configs=None,
                   node_groups=None, user_keypair_id=None,
                   anti_affinity=None, net_id=None):
    return client(request).clusters.create(name, plugin_name, hadoop_version,
                                           cluster_template_id,
                                           default_image_id,
                                           is_transient, description,
                                           cluster_configs, node_groups,
                                           user_keypair_id, anti_affinity,
                                           net_id)


def cluster_scale(request, cluster_id, scale_object):
    return client(request).clusters.scale(cluster_id, scale_object)


def cluster_list(request):
    return client(request).clusters.list()


def cluster_get(request, cluster_id):
    return client(request).clusters.get(cluster_id)


def cluster_delete(request, cluster_id):
    client(request).clusters.delete(cluster_id)


def data_source_create(request, name, description, ds_type, url,
                       credential_user=None, credential_pass=None):
    return client(request).data_sources.create(name, description, ds_type,
                                               url, credential_user,
                                               credential_pass)


def data_source_list(request):
    return client(request).data_sources.list()


def data_source_get(request, ds_id):
    return client(request).data_sources.get(ds_id)


def data_source_delete(request, ds_id):
    client(request).data_sources.delete(ds_id)


def job_binary_create(request, name, url, description, extra):
    return client(request).job_binaries.create(name, url, description, extra)


def job_binary_list(request):
    return client(request).job_binaries.list()


def job_binary_get(request, jb_id):
    return client(request).job_binaries.get(jb_id)


def job_binary_delete(request, jb_id):
    client(request).job_binaries.delete(jb_id)


def job_binary_get_file(request, jb_id):
    return client(request).job_binaries.get_file(jb_id)


def job_binary_internal_create(request, name, data):
    return client(request).job_binary_internals.create(name, data)


def job_binary_internal_list(request):
    return client(request).job_binary_internals.list()


def job_binary_internal_get(request, jbi_id):
    return client(request).job_binary_internals.get(jbi_id)


def job_binary_internal_delete(request, jbi_id):
    client(request).job_binary_internals.delete(jbi_id)


def job_create(request, name, j_type, mains, libs, description):
    return client(request).jobs.create(name, j_type, mains, libs, description)


def job_list(request):
    return client(request).jobs.list()


def job_get(request, job_id):
    return client(request).jobs.get(job_id)


def job_delete(request, job_id):
    client(request).jobs.delete(job_id)


def job_get_configs(request, job_type):
    return client(request).jobs.get_configs(job_type)


def job_execution_create(request, job_id, cluster_id,
                         input_id, output_id, configs):
    return client(request).job_executions.create(job_id, cluster_id,
                                                 input_id, output_id,
                                                 configs)


def job_execution_list(request):
    jex_list = client(request).job_executions.list()
    job_dict = dict((j.id, j) for j in job_list(request))
    cluster_dict = dict((c.id, c) for c in cluster_list(request))
    for jex in jex_list:
        setattr(jex, 'job_name', job_dict.get(jex.job_id).name)
        setattr(jex, 'cluster_name', cluster_dict.get(jex.cluster_id).name)
    return jex_list


def job_execution_get(request, jex_id):
    return client(request).job_executions.get(jex_id)


def job_execution_delete(request, jex_id):
    client(request).job_executions.delete(jex_id)
