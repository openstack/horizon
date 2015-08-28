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

import copy

from openstack_dashboard.test.test_data import utils

from saharaclient.api import cluster_templates
from saharaclient.api import clusters
from saharaclient.api import data_sources
from saharaclient.api import job_binaries
from saharaclient.api import job_executions
from saharaclient.api import job_types
from saharaclient.api import jobs
from saharaclient.api import node_group_templates
from saharaclient.api import plugins


def data(TEST):
    TEST.plugins = utils.TestDataContainer()
    TEST.plugins_configs = utils.TestDataContainer()
    TEST.nodegroup_templates = utils.TestDataContainer()
    TEST.cluster_templates = utils.TestDataContainer()
    TEST.clusters = utils.TestDataContainer()
    TEST.data_sources = utils.TestDataContainer()
    TEST.job_binaries = utils.TestDataContainer()
    TEST.jobs = utils.TestDataContainer()
    TEST.job_executions = utils.TestDataContainer()
    TEST.registered_images = copy.copy(TEST.images)
    TEST.job_types = utils.TestDataContainer()

    plugin1_dict = {
        "description": "vanilla plugin",
        "name": "vanilla",
        "title": "Vanilla Apache Hadoop",
        "versions": ["2.3.0", "1.2.1"]
    }

    plugin1 = plugins.Plugin(plugins.PluginManager(None), plugin1_dict)

    TEST.plugins.add(plugin1)

    plugin_config1_dict = {
        "node_processes": {
            "HDFS": [
                "namenode",
                "datanode",
                "secondarynamenode"
            ],
            "MapReduce": [
                "tasktracker",
                "jobtracker"
            ]
        },
        "description": "This plugin provides an ability to launch vanilla "
                       "Apache Hadoop cluster without any management "
                       "consoles.",
        "versions": [
            "1.2.1"
        ],
        "required_image_tags": [
            "vanilla",
            "1.2.1"
        ],
        "configs": [
            {
                "default_value": "/tmp/hadoop-${user.name}",
                "name": "hadoop.tmp.dir",
                "priority": 2,
                "config_type": "string",
                "applicable_target": "HDFS",
                "is_optional": True,
                "scope": "node",
                "description": "A base for other temporary directories."
            },
            {
                "default_value": True,
                "name": "hadoop.native.lib",
                "priority": 2,
                "config_type": "bool",
                "applicable_target": "HDFS",
                "is_optional": True,
                "scope": "node",
                "description": "Should native hadoop libraries, if present, "
                               "be used."
            },
        ],
        "title": "Vanilla Apache Hadoop",
        "name": "vanilla"
    }

    TEST.plugins_configs.add(plugins.Plugin(plugins.PluginManager(None),
                                            plugin_config1_dict))

    # Nodegroup_Templates.
    ngt1_dict = {
        "created_at": "2014-06-04 14:01:03.701243",
        "description": None,
        "flavor_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "availability_zone": None,
        "floating_ip_pool": None,
        "auto_security_group": True,
        "security_groups": [],
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
        "volumes_size": 0,
        "volume_type": None,
        "volume_local_to_instance": False,
        "security_groups": [],
        "volumes_availability_zone": None,
    }

    ngt1 = node_group_templates.NodeGroupTemplate(
        node_group_templates.NodeGroupTemplateManager(None), ngt1_dict)

    TEST.nodegroup_templates.add(ngt1)

    # Cluster_templates.
    ct1_dict = {
        "anti_affinity": [],
        "cluster_configs": {},
        "created_at": "2014-06-04 14:01:06.460711",
        "default_image_id": None,
        "description": "Sample description",
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
                "volumes_size": 0,
                "volume_type": None,
                "volume_local_to_instance": False,
                "volumes_availability_zone": None,
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
                "volumes_size": 0,
                "volume_type": None,
                "volume_local_to_instance": False,
                "volumes_availability_zone": None,
            }
        ],
        "plugin_name": "vanilla",
        "tenant_id": "429ad8447c2d47bc8e0382d244e1d1df",
        "updated_at": None
    }

    ct1 = cluster_templates.ClusterTemplate(
        cluster_templates.ClusterTemplateManager(None), ct1_dict)
    TEST.cluster_templates.add(ct1)

    # Clusters.
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
                "volumes_size": 0,
                "volume_type": None,
                "volume_local_to_instance": False,
                "security_groups": [],
                "volumes_availability_zone": None,
                "id": "ng1"
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
                "volumes_size": 0,
                "volume_type": None,
                "volume_local_to_instance": False,
                "security_groups": ["b7857890-09bf-4ee0-a0d5-322d7a6978bf"],
                "volumes_availability_zone": None,
                "id": "ng2"
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

    cluster2_dict = copy.deepcopy(cluster1_dict)
    cluster2_dict.update({
        "id": "cl2",
        "name": "cl2_name",
        "provision_progress": [
            {
                "created_at": "2015-03-27T15:51:54",
                "updated_at": "2015-03-27T15:59:34",
                "step_name": "first_step",
                "step_type": "some_type",
                "successful": True,
                "events": [],
                "total": 3
            },
            {
                "created_at": "2015-03-27T16:01:54",
                "updated_at": "2015-03-27T16:10:22",
                "step_name": "second_step",
                "step_type": "some_other_type",
                "successful": None,
                "events": [
                    {
                        "id": "evt1",
                        "created_at": "2015-03-27T16:01:22",
                        "node_group_id": "ng1",
                        "instance_name": "cercluster-master-001",
                        "successful": True,
                        "event_info": None
                    },
                    {
                        "id": "evt2",
                        "created_at": "2015-03-27T16:04:51",
                        "node_group_id": "ng2",
                        "instance_name": "cercluster-workers-001",
                        "successful": True,
                        "event_info": None
                    }
                ],
                "total": 3
            }
        ]
    })

    cluster2 = clusters.Cluster(
        clusters.ClusterManager(None), cluster2_dict)
    TEST.clusters.add(cluster2)

    # Data Sources.
    data_source1_dict = {
        "created_at": "2014-06-04 14:01:10.371562",
        "description": "sample output",
        "id": "426fb01c-5c7e-472d-bba2-b1f0fe7e0ede",
        "name": "sampleOutput",
        "tenant_id": "429ad8447c2d47bc8e0382d244e1d1df",
        "type": "swift",
        "updated_at": None,
        "url": "swift://example.sahara/output"
    }

    data_source2_dict = {
        "created_at": "2014-06-05 15:01:12.331361",
        "description": "second sample output",
        "id": "ab3413-adfb-bba2-123456785675",
        "name": "sampleOutput2",
        "tenant_id": "429ad8447c2d47bc8e0382d244e1d1df",
        "type": "hdfs",
        "updated_at": None,
        "url": "hdfs://example.sahara/output"
    }

    data_source1 = data_sources.DataSources(
        data_sources.DataSourceManager(None), data_source1_dict)
    data_source2 = data_sources.DataSources(
        data_sources.DataSourceManager(None), data_source2_dict)
    TEST.data_sources.add(data_source1)
    TEST.data_sources.add(data_source2)

    # Job Binaries.
    job_binary1_dict = {
        "created_at": "2014-06-05 18:15:15.581285",
        "description": "",
        "id": "3f3a07ac-7d6f-49e8-8669-40b25ee891b7",
        "name": "example.pig",
        "tenant_id": "429ad8447c2d47bc8e0382d244e1d1df",
        "updated_at": None,
        "url": "internal-db://80121dea-f8bd-4ad3-bcc7-096f4bfc722d"
    }

    job_binary2_dict = {
        "created_at": "2014-10-10 13:12:15.583631",
        "description": "Test for spaces in name",
        "id": "abcdef56-1234-abcd-abcd-defabcdaedcb",
        "name": "example with spaces.pig",
        "tenant_id": "429ad8447c2d47bc8e0382d244e1d1df",
        "updated_at": None,
        "url": "internal-db://abcdef56-1234-abcd-abcd-defabcdaedcb"
    }

    job_binary1 = job_binaries.JobBinaries(
        job_binaries.JobBinariesManager(None), job_binary1_dict)
    job_binary2 = job_binaries.JobBinaries(
        job_binaries.JobBinariesManager(None), job_binary2_dict)

    TEST.job_binaries.add(job_binary1)
    TEST.job_binaries.add(job_binary2)

    # Jobs.
    job1_dict = {
        "created_at": "2014-06-05 19:23:59.637165",
        "description": "",
        "id": "a077b851-46be-4ad7-93c3-2d83894546ef",
        "libs": [
            {
                "created_at": "2014-06-05 19:23:42.742057",
                "description": "",
                "id": "ab140807-59f8-4235-b4f2-e03daf946256",
                "name": "udf.jar",
                "tenant_id": "429ad8447c2d47bc8e0382d244e1d1df",
                "updated_at": None,
                "url": "internal-db://d186e2bb-df93-47eb-8c0e-ce21e7ecb78b"
            }
        ],
        "mains": [
            {
                "created_at": "2014-06-05 18:15:15.581285",
                "description": "",
                "id": "3f3a07ac-7d6f-49e8-8669-40b25ee891b7",
                "name": "example.pig",
                "tenant_id": "429ad8447c2d47bc8e0382d244e1d1df",
                "updated_at": None,
                "url": "internal-db://80121dea-f8bd-4ad3-bcc7-096f4bfc722d"
            }
        ],
        "name": "pigjob",
        "tenant_id": "429ad8447c2d47bc8e0382d244e1d1df",
        "type": "Pig",
        "updated_at": None
    }

    job1 = jobs.Job(jobs.JobsManager(None), job1_dict)
    TEST.jobs.add(job1)

    # Job Executions.
    jobex1_dict = {
        "cluster_id": "ec9a0d28-5cfb-4028-a0b5-40afe23f1533",
        "created_at": "2014-06-05 20:03:06.195937",
        "end_time": None,
        "id": "4b6c1cbf-c713-49d3-8025-808a87c514a6",
        "info": {
            "acl": None,
            "actions": [
                {
                    "consoleUrl": "-",
                    "cred": "None",
                    "data": None,
                    "endTime": "Thu,05 Jun 2014 20:03:32 GMT",
                    "errorCode": None,
                    "errorMessage": None,
                    "externalChildIDs": None,
                    "externalId": "-",
                    "externalStatus": "OK",
                    "id": "0000000-140604200538581-oozie-hado-W@:start:",
                    "name": ":start:",
                    "retries": 0,
                    "startTime": "Thu,05 Jun 2014 20:03:32 GMT",
                    "stats": None,
                    "status": "OK",
                    "toString": "Action name[:start:] status[OK]",
                    "trackerUri": "-",
                    "transition": "job-node",
                    "type": ":START:"
                },
                {
                    "consoleUrl": "fake://console.url",
                    "cred": "None",
                    "data": None,
                    "endTime": None,
                    "errorCode": None,
                    "errorMessage": None,
                    "externalChildIDs": None,
                    "externalId": "job_201406042004_0001",
                    "externalStatus": "RUNNING",
                    "id": "0000000-140604200538581-oozie-hado-W@job-node",
                    "name": "job-node",
                    "retries": 0,
                    "startTime": "Thu,05 Jun 2014 20:03:33 GMT",
                    "stats": None,
                    "status": "RUNNING",
                    "toString": "Action name[job-node] status[RUNNING]",
                    "trackerUri": "cercluster-master-001:8021",
                    "transition": None,
                    "type": "pig"
                }
            ],
            "appName": "job-wf",
            "appPath": "hdfs://fakepath/workflow.xml",
            "conf": "<configuration>fakeconfig</configuration>",
            "consoleUrl": "fake://consoleURL",
            "createdTime": "Thu,05 Jun 2014 20:03:32 GMT",
            "endTime": None,
            "externalId": None,
            "group": None,
            "id": "0000000-140604200538581-oozie-hado-W",
            "lastModTime": "Thu,05 Jun 2014 20:03:35 GMT",
            "parentId": None,
            "run": 0,
            "startTime": "Thu,05 Jun 2014 20:03:32 GMT",
            "status": "RUNNING",
            "toString": "Workflow ...status[RUNNING]",
            "user": "hadoop"
        },
        "input_id": "85884883-3083-49eb-b442-71dd3734d02c",
        "job_configs": {
            "args": [],
            "configs": {},
            "params": {}
        },
        "job_id": "a077b851-46be-4ad7-93c3-2d83894546ef",
        "oozie_job_id": "0000000-140604200538581-oozie-hado-W",
        "output_id": "426fb01c-5c7e-472d-bba2-b1f0fe7e0ede",
        "progress": None,
        "return_code": None,
        "start_time": "2014-06-05T16:03:32",
        "tenant_id": "429ad8447c2d47bc8e0382d244e1d1df",
        "updated_at": "2014-06-05 20:03:46.438248",
        "cluster_name_set": True,
        "job_name_set": True,
        "cluster_name": "cluster-1",
        "job_name": "job-1",
        "data_source_urls": {
            "85884883-3083-49eb-b442-71dd3734d02c": "swift://a.sahara/input",
            "426fb01c-5c7e-472d-bba2-b1f0fe7e0ede": "hdfs://a.sahara/output"
        }
    }

    jobex1 = job_executions.JobExecution(
        job_executions.JobExecutionsManager(None), jobex1_dict)
    TEST.job_executions.add(jobex1)

    augmented_image = TEST.registered_images.first()
    augmented_image.tags = {}
    augmented_image.username = 'myusername'
    augmented_image.description = 'mydescription'

    job_type1_dict = {
        "name": "Pig",
        "plugins": [
            {
                "description": "Fake description",
                "versions": {
                    "2.6.0": {
                    },
                    "1.2.1": {
                    }
                },
                "name": "vanilla",
                "title": "Vanilla Apache Hadoop"
            },
        ]
    }
    job_types1 = job_types.JobType(
        job_types.JobTypesManager(None), job_type1_dict)
    TEST.job_types.add(job_types1)
