# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from openstack_dashboard.test.test_data import utils

from saharaclient.api import node_group_templates
from saharaclient.api import plugins


def data(TEST):
    TEST.plugins = utils.TestDataContainer()
    TEST.nodegroup_templates = utils.TestDataContainer()

    plugin1_dict = {
        "description": "vanilla plugin",
        "name": "vanilla",
        "title": "Vanilla Apache Hadoop",
        "versions": ["2.3.0", "1.2.1"]
    }

    plugin1 = plugins.Plugin(plugins.PluginManager(None), plugin1_dict)

    TEST.plugins.add(plugin1)

    #Nodegroup_Templates
    ngt1_dict = {
        "created_at": "2014-06-04 14:01:03.701243",
        "description": None,
        "flavor_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "floating_ip_pool": None,
        "hadoop_version": "1.2.1",
        "id": "c166dfcc-9cc7-4b48-adc9-f0946169bb36",
        "image_id": None,
        "name": "sample-template",
        "node_configs": {},
        "node_processes": [
            "namenode",
            "jobtracker",
            "secondarynamenode",
            "hiveserver",
            "oozie"
        ],
        "plugin_name": "vanilla",
        "tenant_id": "429ad8447c2d47bc8e0382d244e1d1df",
        "updated_at": None,
        "volume_mount_prefix": "/volumes/disk",
        "volumes_per_node": 0,
        "volumes_size": 0
    }

    ngt1 = node_group_templates.NodeGroupTemplate(
        node_group_templates.NodeGroupTemplateManager(None), ngt1_dict)

    TEST.nodegroup_templates.add(ngt1)
