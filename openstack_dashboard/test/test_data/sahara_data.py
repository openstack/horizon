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

from saharaclient.api import cluster_templates
from saharaclient.api import clusters
from saharaclient.api import node_group_templates
from saharaclient.api import plugins


def data(TEST):
    TEST.plugins = utils.TestDataContainer()
    TEST.nodegroup_templates = utils.TestDataContainer()
    TEST.cluster_templates = utils.TestDataContainer()
    TEST.clusters = utils.TestDataContainer()

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

    #Cluster_templates
    ct1_dict = {
        "anti_affinity": [],
        "cluster_configs": {},
        "created_at": "2014-06-04 14:01:06.460711",
        "default_image_id": None,
        "description": None,
        "hadoop_version": "1.2.1",
        "id": "a2c3743f-31a2-4919-8d02-792138a87a98",
        "name": "sample-cluster-template",
        "neutron_management_network": None,
        "node_groups": [
            {
                "count": 1,
                "created_at": "2014-06-04 14:01:06.462512",
                "flavor_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "floating_ip_pool": None,
                "image_id": None,
                "name": "master",
                "node_configs": {},
                "node_group_template_id": "c166dfcc-9cc7-4b48-adc9",
                "node_processes": [
                    "namenode",
                    "jobtracker",
                    "secondarynamenode",
                    "hiveserver",
                    "oozie"
                ],
                "updated_at": None,
                "volume_mount_prefix": "/volumes/disk",
                "volumes_per_node": 0,
                "volumes_size": 0
            },
            {
                "count": 2,
                "created_at": "2014-06-04 14:01:06.463214",
                "flavor_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "floating_ip_pool": None,
                "image_id": None,
                "name": "workers",
                "node_configs": {},
                "node_group_template_id": "4eb5504c-94c9-4049-a440",
                "node_processes": [
                    "datanode",
                    "tasktracker"
                ],
                "updated_at": None,
                "volume_mount_prefix": "/volumes/disk",
                "volumes_per_node": 0,
                "volumes_size": 0
            }
        ],
        "plugin_name": "vanilla",
        "tenant_id": "429ad8447c2d47bc8e0382d244e1d1df",
        "updated_at": None
    }

    ct1 = cluster_templates.ClusterTemplate(
        cluster_templates.ClusterTemplateManager(None), ct1_dict)
    TEST.cluster_templates.add(ct1)

    #Clusters
    cluster1_dict = {
        "anti_affinity": [],
        "cluster_configs": {},
        "cluster_template_id": "a2c3743f-31a2-4919-8d02-792138a87a98",
        "created_at": "2014-06-04 20:02:14.051328",
        "default_image_id": "9eb4643c-dca8-4ea7-92d2-b773f88a8dc6",
        "description": "",
        "hadoop_version": "1.2.1",
        "id": "ec9a0d28-5cfb-4028-a0b5-40afe23f1533",
        "info": {},
        "is_transient": False,
        "management_public_key": "fakekey",
        "name": "cercluster",
        "neutron_management_network": None,
        "node_groups": [
            {
                "count": 1,
                "created_at": "2014-06-04 20:02:14.053153",
                "flavor_id": "0",
                "floating_ip_pool": None,
                "image_id": None,
                "instances": [
                    {
                        "created_at": "2014-06-04 20:02:14.834529",
                        "id": "c3b8004b-7063-4b99-a082-820cdc6e961c",
                        "instance_id": "a45f5495-4a10-4f17-8fae",
                        "instance_name": "cercluster-master-001",
                        "internal_ip": None,
                        "management_ip": None,
                        "updated_at": None,
                        "volumes": []
                    }
                ],
                "name": "master",
                "node_configs": {},
                "node_group_template_id": "c166dfcc-9cc7-4b48-adc9",
                "node_processes": [
                    "namenode",
                    "jobtracker",
                    "secondarynamenode",
                    "hiveserver",
                    "oozie"
                ],
                "updated_at": "2014-06-04 20:02:14.841760",
                "volume_mount_prefix": "/volumes/disk",
                "volumes_per_node": 0,
                "volumes_size": 0
            },
            {
                "count": 2,
                "created_at": "2014-06-04 20:02:14.053849",
                "flavor_id": "0",
                "floating_ip_pool": None,
                "image_id": None,
                "instances": [
                    {
                        "created_at": "2014-06-04 20:02:15.097655",
                        "id": "6a8ae0b1-bb28-4de2-bfbb-bdd3fd2d72b2",
                        "instance_id": "38bf8168-fb30-483f-8d52",
                        "instance_name": "cercluster-workers-001",
                        "internal_ip": None,
                        "management_ip": None,
                        "updated_at": None,
                        "volumes": []
                    },
                    {
                        "created_at": "2014-06-04 20:02:15.344515",
                        "id": "17b98ed3-a776-467a-90cf-9f46a841790b",
                        "instance_id": "85606938-8e53-46a5-a50b",
                        "instance_name": "cercluster-workers-002",
                        "internal_ip": None,
                        "management_ip": None,
                        "updated_at": None,
                        "volumes": []
                    }
                ],
                "name": "workers",
                "node_configs": {},
                "node_group_template_id": "4eb5504c-94c9-4049-a440",
                "node_processes": [
                    "datanode",
                    "tasktracker"
                ],
                "updated_at": "2014-06-04 20:02:15.355745",
                "volume_mount_prefix": "/volumes/disk",
                "volumes_per_node": 0,
                "volumes_size": 0
            }
        ],
        "plugin_name": "vanilla",
        "status": "Active",
        "status_description": "",
        "tenant_id": "429ad8447c2d47bc8e0382d244e1d1df",
        "trust_id": None,
        "updated_at": "2014-06-04 20:02:15.446087",
        "user_keypair_id": "stackboxkp"
    }

    cluster1 = clusters.Cluster(
        clusters.ClusterManager(None), cluster1_dict)
    TEST.clusters.add(cluster1)
