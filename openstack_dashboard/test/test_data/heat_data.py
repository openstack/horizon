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

from heatclient.v1 import resource_types
from heatclient.v1 import resources
from heatclient.v1 import services
from heatclient.v1 import stacks

from openstack_dashboard.test.test_data import utils


# A slightly hacked up copy of a sample cloudformation template for testing.
TEMPLATE = """
{
"AWSTemplateFormatVersion": "2010-09-09",
"Description": "AWS CloudFormation Sample Template.",
"Parameters": {
"KeyName": {
"Description": "Name of an EC2 Key Pair to enable SSH access to the instances",
"Type": "String"
},
"InstanceType": {
"Description": "WebServer EC2 instance type",
"Type": "String",
"Default": "m1.small",
"AllowedValues": [
"m1.tiny",
"m1.small",
"m1.medium",
"m1.large",
"m1.xlarge"
],
"ConstraintDescription": "must be a valid EC2 instance type."
},
"DBName": {
"Default": "wordpress",
"Description": "The WordPress database name",
"Type": "String",
"MinLength": "1",
"MaxLength": "64",
"AllowedPattern": "[a-zA-Z][a-zA-Z0-9]*",
"ConstraintDescription": "must begin with a letter and..."
},
"DBUsername": {
"Default": "admin",
"NoEcho": "true",
"Description": "The WordPress database admin account username",
"Type": "String",
"MinLength": "1",
"MaxLength": "16",
"AllowedPattern": "[a-zA-Z][a-zA-Z0-9]*",
"ConstraintDescription": "must begin with a letter and..."
},
"DBPassword": {
"Default": "admin",
"NoEcho": "true",
"Description": "The WordPress database admin account password",
"Type": "String",
"MinLength": "1",
"MaxLength": "41",
"AllowedPattern": "[a-zA-Z0-9]*",
"ConstraintDescription": "must contain only alphanumeric characters."
},
"DBRootPassword": {
"Default": "admin",
"NoEcho": "true",
"Description": "Root password for MySQL",
"Type": "String",
"MinLength": "1",
"MaxLength": "41",
"AllowedPattern": "[a-zA-Z0-9]*",
"ConstraintDescription": "must contain only alphanumeric characters."
},
"LinuxDistribution": {
"Default": "F17",
"Description": "Distribution of choice",
"Type": "String",
"AllowedValues": [
"F18",
"F17",
"U10",
"RHEL-6.1",
"RHEL-6.2",
"RHEL-6.3"
]
},
"Network": {
"Type": "String",
"CustomConstraint": "neutron.network"
}
},
"Mappings": {
"AWSInstanceType2Arch": {
"m1.tiny": {
"Arch": "32"
},
"m1.small": {
"Arch": "64"
},
"m1.medium": {
"Arch": "64"
},
"m1.large": {
"Arch": "64"
},
"m1.xlarge": {
"Arch": "64"
}
},
"DistroArch2AMI": {
"F18": {
"32": "F18-i386-cfntools",
"64": "F18-x86_64-cfntools"
},
"F17": {
"32": "F17-i386-cfntools",
"64": "F17-x86_64-cfntools"
},
"U10": {
"32": "U10-i386-cfntools",
"64": "U10-x86_64-cfntools"
},
"RHEL-6.1": {
"32": "rhel61-i386-cfntools",
"64": "rhel61-x86_64-cfntools"
},
"RHEL-6.2": {
"32": "rhel62-i386-cfntools",
"64": "rhel62-x86_64-cfntools"
},
"RHEL-6.3": {
"32": "rhel63-i386-cfntools",
"64": "rhel63-x86_64-cfntools"
}
}
},
"Resources": {
"WikiDatabase": {
"Type": "AWS::EC2::Instance",
"Metadata": {
"AWS::CloudFormation::Init": {
"config": {
"packages": {
"yum": {
"mysql": [],
"mysql-server": [],
"httpd": [],
"wordpress": []
}
},
"services": {
"systemd": {
"mysqld": {
"enabled": "true",
"ensureRunning": "true"
},
"httpd": {
"enabled": "true",
"ensureRunning": "true"
}
}
}
}
}
},
"Properties": {
"ImageId": {
"Fn::FindInMap": [
"DistroArch2AMI",
{
"Ref": "LinuxDistribution"
},
{
"Fn::FindInMap": [
"AWSInstanceType2Arch",
{
"Ref": "InstanceType"
},
"Arch"
]
}
]
},
"InstanceType": {
"Ref": "InstanceType"
},
"KeyName": {
"Ref": "KeyName"
},
"UserData": {
"Fn::Base64": {
"Fn::Join": [
"",
[
"#!/bin/bash -v\n",
"/opt/aws/bin/cfn-init\n"
]
]
}
}
}
}
},
"Outputs": {
"WebsiteURL": {
"Value": {
"Fn::Join": [
"",
[
"http://",
{
"Fn::GetAtt": [
"WikiDatabase",
"PublicIp"
]
},
"/wordpress"
]
]
},
"Description": "URL for Wordpress wiki"
}
}
}
"""

VALIDATE = """
{
"Description": "AWS CloudFormation Sample Template.",
"Parameters": {
"DBUsername": {
"Type": "String",
"Description": "The WordPress database admin account username",
"Default": "admin",
"MinLength": "1",
"AllowedPattern": "[a-zA-Z][a-zA-Z0-9]*",
"NoEcho": "true",
"MaxLength": "16",
"ConstraintDescription": "must begin with a letter and..."
},
"LinuxDistribution": {
"Default": "F17",
"Type": "String",
"Description": "Distribution of choice",
"AllowedValues": [
"F18",
"F17",
"U10",
"RHEL-6.1",
"RHEL-6.2",
"RHEL-6.3"
]
},
"DBRootPassword": {
"Type": "String",
"Description": "Root password for MySQL",
"Default": "admin",
"MinLength": "1",
"AllowedPattern": "[a-zA-Z0-9]*",
"NoEcho": "true",
"MaxLength": "41",
"ConstraintDescription": "must contain only alphanumeric characters."
},
"KeyName": {
"Type": "String",
"Description": "Name of an EC2 Key Pair to enable SSH access to the instances"
},
"DBName": {
"Type": "String",
"Description": "The WordPress database name",
"Default": "wordpress",
"MinLength": "1",
"AllowedPattern": "[a-zA-Z][a-zA-Z0-9]*",
"MaxLength": "64",
"ConstraintDescription": "must begin with a letter and..."
},
"DBPassword": {
"Type": "String",
"Description": "The WordPress database admin account password",
"Default": "admin",
"MinLength": "1",
"AllowedPattern": "[a-zA-Z0-9]*",
"NoEcho": "true",
"MaxLength": "41",
"ConstraintDescription": "must contain only alphanumeric characters."
},
"InstanceType": {
"Default": "m1.small",
"Type": "String",
"ConstraintDescription": "must be a valid EC2 instance type.",
"Description": "WebServer EC2 instance type",
"AllowedValues": [
"m1.tiny",
"m1.small",
"m1.medium",
"m1.large",
"m1.xlarge"
]
},
"Network": {
"Type": "String",
"CustomConstraint": "neutron.network"
}
}
}
"""

ENVIRONMENT = """
parameters:
  InstanceType: m1.xsmall
  db_password: verybadpass
  KeyName: heat_key
"""


class Environment(object):
    def __init__(self, data):
        self.data = data


class Template(object):
    def __init__(self, data, validate):
        self.data = data
        self.validate = validate


def data(TEST):
    TEST.stacks = utils.TestDataContainer()
    TEST.stack_templates = utils.TestDataContainer()
    TEST.stack_environments = utils.TestDataContainer()
    TEST.resource_types = utils.TestDataContainer()
    TEST.heat_resources = utils.TestDataContainer()
    TEST.heat_services = utils.TestDataContainer()

    # Services
    service_1 = services.Service(services.ServiceManager(None), {
        "status": "up",
        "binary": "heat-engine",
        "report_interval": 60,
        "engine_id": "2f7b5a9b-c50b-4b01-8248-f89f5fb338d1",
        "created_at": "2015-02-06T03:23:32.000000",
        "hostname": "mrkanag",
        "updated_at": "2015-02-20T09:49:52.000000",
        "topic": "engine",
        "host": "engine-1",
        "deleted_at": None,
        "id": "1efd7015-5016-4caa-b5c8-12438af7b100"
    })

    service_2 = services.Service(services.ServiceManager(None), {
        "status": "up",
        "binary": "heat-engine",
        "report_interval": 60,
        "engine_id": "2f7b5a9b-c50b-4b01-8248-f89f5fb338d2",
        "created_at": "2015-02-06T03:23:32.000000",
        "hostname": "mrkanag",
        "updated_at": "2015-02-20T09:49:52.000000",
        "topic": "engine",
        "host": "engine-2",
        "deleted_at": None,
        "id": "1efd7015-5016-4caa-b5c8-12438af7b100"
    })

    TEST.heat_services.add(service_1)
    TEST.heat_services.add(service_2)

    # Data return by heatclient.
    TEST.api_resource_types = utils.TestDataContainer()

    for i in range(10):
        stack_data = {
            "description": "No description",
            "links": [{
                "href": "http://192.168.1.70:8004/v1/"
                        "051c727ee67040d6a7b7812708485a97/"
                        "stacks/stack-test{0}/"
                        "05b4f39f-ea96-4d91-910c-e758c078a089{0}".format(i),
                "rel": "self"
            }],
            "parameters": {
                'DBUsername': '******',
                'InstanceType': 'm1.small',
                'AWS::StackId': (
                    'arn:openstack:heat::2ce287:stacks/teststack/88553ec'),
                'DBRootPassword': '******',
                'AWS::StackName': "teststack{0}".format(i),
                'DBPassword': '******',
                'AWS::Region': 'ap-southeast-1',
                'DBName': u'wordpress'
            },
            "stack_status_reason": "Stack successfully created",
            "stack_name": "stack-test{0}".format(i),
            "creation_time": "2013-04-22T00:11:39Z",
            "updated_time": "2013-04-22T00:11:39Z",
            "stack_status": "CREATE_COMPLETE",
            "id": "05b4f39f-ea96-4d91-910c-e758c078a089{0}".format(i)
        }
        stack = stacks.Stack(stacks.StackManager(None), stack_data)
        TEST.stacks.add(stack)

    TEST.stack_templates.add(Template(TEMPLATE, VALIDATE))
    TEST.stack_environments.add(Environment(ENVIRONMENT))

    # Resource types list
    r_type_1 = {
        "resource_type": "AWS::CloudFormation::Stack",
        "attributes": {},
        "properties": {
            "Parameters": {
                "description":
                    "The set of parameters passed to this nested stack.",
                "immutable": False,
                "required": False,
                "type": "map",
                "update_allowed": True},
            "TemplateURL": {
                "description": "The URL of a template that specifies"
                               " the stack to be created as a resource.",
                "immutable": False,
                "required": True,
                "type": "string",
                "update_allowed": True},
            "TimeoutInMinutes": {
                "description": "The length of time, in minutes,"
                               " to wait for the nested stack creation.",
                "immutable": False,
                "required": False,
                "type": "number",
                "update_allowed": True}
        }
    }

    r_type_2 = {
        "resource_type": "OS::Heat::CloudConfig",
        "attributes": {
            "config": {
                "description": "The config value of the software config."}
        },
        "properties": {
            "cloud_config": {
                "description": "Map representing the cloud-config data"
                               " structure which will be formatted as YAML.",
                "immutable": False,
                "required": False,
                "type": "map",
                "update_allowed": False}
        }
    }

    r_types_list = [r_type_1, r_type_2]

    for rt in r_types_list:
        r_type = resource_types.ResourceType(
            resource_types.ResourceTypeManager(None), rt['resource_type'])
        TEST.resource_types.add(r_type)
        TEST.api_resource_types.add(rt)

    # Resources
    resource_1 = resources.Resource(resources.ResourceManager(None), {
        "logical_resource_id": "my_resource",
        "physical_resource_id": "7b5e29b1-c94d-402d-b69c-df9ac6dfc0ce",
        "resource_name": "my_resource",
        "links": [
            {
                "href": "http://192.168.1.70:8004/v1/"
                        "051c727ee67040d6a7b7812708485a97/"
                        "stacks/%s/%s/resources/my_resource" %
                        (TEST.stacks.first().stack_name,
                         TEST.stacks.first().id),
                "rel": "self"
            },
            {
                "href": "http://192.168.1.70:8004/v1/"
                        "051c727ee67040d6a7b7812708485a97/"
                        "stacks/%s/%s" %
                        (TEST.stacks.first().stack_name,
                         TEST.stacks.first().id),
                "rel": "stack"
            }
        ],
        "attributes": {
            "metadata": {}
        }
    })

    TEST.heat_resources.add(resource_1)
