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

import json
import uuid

from novaclient.v2 import aggregates
from novaclient.v2 import availability_zones
from novaclient.v2 import certs
from novaclient.v2 import flavor_access
from novaclient.v2 import flavors
from novaclient.v2 import floating_ips
from novaclient.v2 import hosts
from novaclient.v2 import hypervisors
from novaclient.v2 import keypairs
from novaclient.v2 import quotas
from novaclient.v2 import security_group_rules as rules
from novaclient.v2 import security_groups as sec_groups
from novaclient.v2 import servers
from novaclient.v2 import services
from novaclient.v2 import usage
from novaclient.v2 import volume_snapshots as vol_snaps
from novaclient.v2 import volume_types
from novaclient.v2 import volumes

from openstack_dashboard.api import base
from openstack_dashboard.api import nova
from openstack_dashboard.usage import quotas as usage_quotas

from openstack_dashboard.test.test_data import utils


class FlavorExtraSpecs(dict):
    def __repr__(self):
        return "<FlavorExtraSpecs %s>" % self._info

    def __init__(self, info):
        super(FlavorExtraSpecs, self).__init__()
        self.__dict__.update(info)
        self.update(info)
        self._info = info


SERVER_DATA = """
{
    "server": {
        "OS-EXT-SRV-ATTR:instance_name": "instance-00000005",
        "OS-EXT-SRV-ATTR:host": "instance-host",
        "OS-EXT-STS:task_state": null,
        "addresses": {
            "private": [
                {
                    "version": 4,
                    "addr": "10.0.0.1"
                }
            ]
        },
        "links": [
            {
                "href": "%(host)s/v1.1/%(tenant_id)s/servers/%(server_id)s",
                "rel": "self"
            },
            {
                "href": "%(host)s/%(tenant_id)s/servers/%(server_id)s",
                "rel": "bookmark"
            }
        ],
        "image": {
            "id": "%(image_id)s",
            "links": [
                {
                    "href": "%(host)s/%(tenant_id)s/images/%(image_id)s",
                    "rel": "bookmark"
                }
            ]
        },
        "OS-EXT-STS:vm_state": "active",
        "flavor": {
            "id": "%(flavor_id)s",
            "links": [
                {
                    "href": "%(host)s/%(tenant_id)s/flavors/%(flavor_id)s",
                    "rel": "bookmark"
                }
            ]
        },
        "id": "%(server_id)s",
        "user_id": "%(user_id)s",
        "OS-DCF:diskConfig": "MANUAL",
        "accessIPv4": "",
        "accessIPv6": "",
        "progress": null,
        "OS-EXT-STS:power_state": 1,
        "config_drive": "",
        "status": "%(status)s",
        "updated": "2012-02-28T19:51:27Z",
        "hostId": "c461ea283faa0ab5d777073c93b126c68139e4e45934d4fc37e403c2",
        "key_name": "%(key_name)s",
        "name": "%(name)s",
        "created": "2012-02-28T19:51:17Z",
        "tenant_id": "%(tenant_id)s",
        "metadata": {"someMetaLabel": "someMetaData",
                     "some<b>html</b>label": "<!--",
                     "empty": ""}
    }
}
"""


USAGE_DATA = """
{
    "total_memory_mb_usage": 64246.89777777778,
    "total_vcpus_usage": 125.48222222222223,
    "total_hours": 125.48222222222223,
    "total_local_gb_usage": 0,
    "tenant_id": "%(tenant_id)s",
    "stop": "2012-01-31 23:59:59",
    "start": "2012-01-01 00:00:00",
    "server_usages": [
        {
            "memory_mb": %(flavor_ram)s,
            "uptime": 442321,
            "started_at": "2012-01-26 20:38:21",
            "ended_at": null,
            "name": "%(instance_name)s",
            "tenant_id": "%(tenant_id)s",
            "state": "active",
            "hours": 122.87361111111112,
            "vcpus": %(flavor_vcpus)s,
            "flavor": "%(flavor_name)s",
            "local_gb": %(flavor_disk)s
        },
        {
            "memory_mb": %(flavor_ram)s,
            "uptime": 9367,
            "started_at": "2012-01-31 20:54:15",
            "ended_at": null,
            "name": "%(instance_name)s",
            "tenant_id": "%(tenant_id)s",
            "state": "active",
            "hours": 2.608611111111111,
            "vcpus": %(flavor_vcpus)s,
            "flavor": "%(flavor_name)s",
            "local_gb": %(flavor_disk)s
        }
    ]
}
"""


def data(TEST):
    TEST.servers = utils.TestDataContainer()
    TEST.flavors = utils.TestDataContainer()
    TEST.flavor_access = utils.TestDataContainer()
    TEST.keypairs = utils.TestDataContainer()
    TEST.security_groups = utils.TestDataContainer()
    TEST.security_groups_uuid = utils.TestDataContainer()
    TEST.security_group_rules = utils.TestDataContainer()
    TEST.security_group_rules_uuid = utils.TestDataContainer()
    TEST.volumes = utils.TestDataContainer()
    TEST.quotas = utils.TestDataContainer()
    TEST.quota_usages = utils.TestDataContainer()
    TEST.disabled_quotas = utils.TestDataContainer()
    TEST.floating_ips = utils.TestDataContainer()
    TEST.floating_ips_uuid = utils.TestDataContainer()
    TEST.usages = utils.TestDataContainer()
    TEST.certs = utils.TestDataContainer()
    TEST.volume_snapshots = utils.TestDataContainer()
    TEST.volume_types = utils.TestDataContainer()
    TEST.availability_zones = utils.TestDataContainer()
    TEST.hypervisors = utils.TestDataContainer()
    TEST.services = utils.TestDataContainer()
    TEST.aggregates = utils.TestDataContainer()
    TEST.hosts = utils.TestDataContainer()

    # Data return by novaclient.
    # It is used if API layer does data conversion.
    TEST.api_floating_ips = utils.TestDataContainer()
    TEST.api_floating_ips_uuid = utils.TestDataContainer()

    # Volumes
    volume = volumes.Volume(
        volumes.VolumeManager(None),
        {"id": "41023e92-8008-4c8b-8059-7f2293ff3775",
         "name": 'test_volume',
         "status": 'available',
         "size": 40,
         "display_name": 'Volume name',
         "created_at": '2012-04-01 10:30:00',
         "volume_type": None,
         "attachments": []})
    nameless_volume = volumes.Volume(
        volumes.VolumeManager(None),
        {"id": "3b189ac8-9166-ac7f-90c9-16c8bf9e01ac",
         "name": '',
         "status": 'in-use',
         "size": 10,
         "display_name": '',
         "display_description": '',
         "device": "/dev/hda",
         "created_at": '2010-11-21 18:34:25',
         "volume_type": 'vol_type_1',
         "attachments": [{"id": "1", "server_id": '1',
                          "device": "/dev/hda"}]})
    attached_volume = volumes.Volume(
        volumes.VolumeManager(None),
        {"id": "8cba67c1-2741-6c79-5ab6-9c2bf8c96ab0",
         "name": 'my_volume',
         "status": 'in-use',
         "size": 30,
         "display_name": 'My Volume',
         "display_description": '',
         "device": "/dev/hdk",
         "created_at": '2011-05-01 11:54:33',
         "volume_type": 'vol_type_2',
         "attachments": [{"id": "2", "server_id": '1',
                          "device": "/dev/hdk"}]})
    non_bootable_volume = volumes.Volume(
        volumes.VolumeManager(None),
        {"id": "41023e92-8008-4c8b-8059-7f2293ff3771",
         "name": 'non_bootable_volume',
         "status": 'available',
         "size": 40,
         "display_name": 'Non Bootable Volume',
         "created_at": '2012-04-01 10:30:00',
         "volume_type": None,
         "attachments": []})

    volume.bootable = 'true'
    nameless_volume.bootable = 'true'
    attached_volume.bootable = 'true'
    non_bootable_volume.bootable = 'false'

    TEST.volumes.add(volume)
    TEST.volumes.add(nameless_volume)
    TEST.volumes.add(attached_volume)
    TEST.volumes.add(non_bootable_volume)

    vol_type1 = volume_types.VolumeType(volume_types.VolumeTypeManager(None),
                                        {'id': 1,
                                         'name': 'vol_type_1'})
    vol_type2 = volume_types.VolumeType(volume_types.VolumeTypeManager(None),
                                        {'id': 2,
                                         'name': 'vol_type_2'})
    TEST.volume_types.add(vol_type1, vol_type2)

    # Flavors
    flavor_1 = flavors.Flavor(flavors.FlavorManager(None),
                              {'id': "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                               'name': 'm1.tiny',
                               'vcpus': 1,
                               'disk': 0,
                               'ram': 512,
                               'swap': 0,
                               'rxtx_factor': 1,
                               'extra_specs': {},
                               'os-flavor-access:is_public': True,
                               'OS-FLV-EXT-DATA:ephemeral': 0})
    flavor_2 = flavors.Flavor(flavors.FlavorManager(None),
                              {'id': "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                               'name': 'm1.massive',
                               'vcpus': 1000,
                               'disk': 1024,
                               'ram': 10000,
                               'swap': 0,
                               'rxtx_factor': 1,
                               'extra_specs': {'Trusted': True, 'foo': 'bar'},
                               'os-flavor-access:is_public': True,
                               'OS-FLV-EXT-DATA:ephemeral': 2048})
    flavor_3 = flavors.Flavor(flavors.FlavorManager(None),
                              {'id': "dddddddd-dddd-dddd-dddd-dddddddddddd",
                               'name': 'm1.secret',
                               'vcpus': 1000,
                               'disk': 1024,
                               'ram': 10000,
                               'swap': 0,
                               'rxtx_factor': 1,
                               'extra_specs': {},
                               'os-flavor-access:is_public': False,
                               'OS-FLV-EXT-DATA:ephemeral': 2048})
    flavor_4 = flavors.Flavor(flavors.FlavorManager(None),
                              {'id': "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
                               'name': 'm1.metadata',
                               'vcpus': 1000,
                               'disk': 1024,
                               'ram': 10000,
                               'swap': 0,
                               'rxtx_factor': 1,
                               'extra_specs': FlavorExtraSpecs(
                                   {'key': 'key_mock',
                                    'value': 'value_mock'}),
                               'os-flavor-access:is_public': False,
                               'OS-FLV-EXT-DATA:ephemeral': 2048})
    TEST.flavors.add(flavor_1, flavor_2, flavor_3, flavor_4)

    flavor_access_manager = flavor_access.FlavorAccessManager(None)
    flavor_access_1 = flavor_access.FlavorAccess(
        flavor_access_manager,
        {"tenant_id": "1",
         "flavor_id": "dddddddd-dddd-dddd-dddd-dddddddddddd"})
    flavor_access_2 = flavor_access.FlavorAccess(
        flavor_access_manager,
        {"tenant_id": "2",
         "flavor_id": "dddddddd-dddd-dddd-dddd-dddddddddddd"})
    TEST.flavor_access.add(flavor_access_1, flavor_access_2)

    # Key pairs
    keypair = keypairs.Keypair(keypairs.KeypairManager(None),
                               dict(name='keyName'))
    TEST.keypairs.add(keypair)

    # Security Groups and Rules
    def generate_security_groups(is_uuid=False):

        def get_id(is_uuid):
            global current_int_id
            if is_uuid:
                return str(uuid.uuid4())
            else:
                get_id.current_int_id += 1
                return get_id.current_int_id

        get_id.current_int_id = 0

        sg_manager = sec_groups.SecurityGroupManager(None)
        rule_manager = rules.SecurityGroupRuleManager(None)

        sec_group_1 = sec_groups.SecurityGroup(sg_manager,
                                               {"rules": [],
                                                "tenant_id": TEST.tenant.id,
                                                "id": get_id(is_uuid),
                                                "name": u"default",
                                                "description": u"default"})
        sec_group_2 = sec_groups.SecurityGroup(sg_manager,
                                               {"rules": [],
                                                "tenant_id": TEST.tenant.id,
                                                "id": get_id(is_uuid),
                                                "name": u"other_group",
                                                "description": u"NotDefault."})
        sec_group_3 = sec_groups.SecurityGroup(sg_manager,
                                               {"rules": [],
                                                "tenant_id": TEST.tenant.id,
                                                "id": get_id(is_uuid),
                                                "name": u"another_group",
                                                "description": u"NotDefault."})

        rule = {'id': get_id(is_uuid),
                'group': {},
                'ip_protocol': u"tcp",
                'from_port': u"80",
                'to_port': u"80",
                'parent_group_id': sec_group_1.id,
                'ip_range': {'cidr': u"0.0.0.0/32"}}

        icmp_rule = {'id': get_id(is_uuid),
                     'group': {},
                     'ip_protocol': u"icmp",
                     'from_port': u"9",
                     'to_port': u"5",
                     'parent_group_id': sec_group_1.id,
                     'ip_range': {'cidr': u"0.0.0.0/32"}}

        group_rule = {'id': 3,
                      'group': {},
                      'ip_protocol': u"tcp",
                      'from_port': u"80",
                      'to_port': u"80",
                      'parent_group_id': sec_group_1.id,
                      'source_group_id': sec_group_1.id}

        rule_obj = rules.SecurityGroupRule(rule_manager, rule)
        rule_obj2 = rules.SecurityGroupRule(rule_manager, icmp_rule)
        rule_obj3 = rules.SecurityGroupRule(rule_manager, group_rule)

        sec_group_1.rules = [rule_obj]
        sec_group_2.rules = [rule_obj]

        return {"rules": [rule_obj, rule_obj2, rule_obj3],
                "groups": [sec_group_1, sec_group_2, sec_group_3]}

    sg_data = generate_security_groups()
    TEST.security_group_rules.add(*sg_data["rules"])
    TEST.security_groups.add(*sg_data["groups"])

    sg_uuid_data = generate_security_groups(is_uuid=True)
    TEST.security_group_rules_uuid.add(*sg_uuid_data["rules"])
    TEST.security_groups_uuid.add(*sg_uuid_data["groups"])

    # Quota Sets
    quota_data = dict(metadata_items='1',
                      injected_file_content_bytes='1',
                      ram=10000,
                      floating_ips='1',
                      fixed_ips='10',
                      instances='10',
                      injected_files='1',
                      cores='10',
                      security_groups='10',
                      security_group_rules='20')
    quota = quotas.QuotaSet(quotas.QuotaSetManager(None), quota_data)
    TEST.quotas.nova = base.QuotaSet(quota)
    TEST.quotas.add(base.QuotaSet(quota))

    # nova quotas disabled when neutron is enabled
    disabled_quotas_nova = ['floating_ips', 'fixed_ips',
                            'security_groups', 'security_group_rules']
    TEST.disabled_quotas.add(disabled_quotas_nova)

    # Quota Usages
    quota_usage_data = {'gigabytes': {'used': 0,
                                      'quota': 1000},
                        'instances': {'used': 0,
                                      'quota': 10},
                        'ram': {'used': 0,
                                'quota': 10000},
                        'cores': {'used': 0,
                                  'quota': 20},
                        'floating_ips': {'used': 0,
                                         'quota': 10},
                        'security_groups': {'used': 0,
                                            'quota': 10},
                        'volumes': {'used': 0,
                                    'quota': 10}}
    quota_usage = usage_quotas.QuotaUsage()
    for k, v in quota_usage_data.items():
        quota_usage.add_quota(base.Quota(k, v['quota']))
        quota_usage.tally(k, v['used'])

    TEST.quota_usages.add(quota_usage)

    # Limits
    limits = {"absolute": {"maxImageMeta": 128,
                           "maxPersonality": 5,
                           "maxPersonalitySize": 10240,
                           "maxSecurityGroupRules": 20,
                           "maxSecurityGroups": 10,
                           "maxServerMeta": 128,
                           "maxTotalCores": 20,
                           "maxTotalFloatingIps": 10,
                           "maxTotalInstances": 10,
                           "maxTotalKeypairs": 100,
                           "maxTotalRAMSize": 10000,
                           "totalCoresUsed": 0,
                           "totalInstancesUsed": 0,
                           "totalKeyPairsUsed": 0,
                           "totalRAMUsed": 0,
                           "totalSecurityGroupsUsed": 0}}
    TEST.limits = limits

    # Servers
    tenant3 = TEST.tenants.list()[2]

    vals = {"host": "http://nova.example.com:8774",
            "name": "server_1",
            "status": "ACTIVE",
            "tenant_id": TEST.tenants.first().id,
            "user_id": TEST.user.id,
            "server_id": "1",
            "flavor_id": flavor_1.id,
            "image_id": TEST.images.first().id,
            "key_name": keypair.name}
    server_1 = servers.Server(servers.ServerManager(None),
                              json.loads(SERVER_DATA % vals)['server'])
    vals.update({"name": "server_2",
                 "status": "BUILD",
                 "server_id": "2"})
    server_2 = servers.Server(servers.ServerManager(None),
                              json.loads(SERVER_DATA % vals)['server'])
    vals.update({"name": u'\u4e91\u89c4\u5219',
                 "status": "ACTIVE",
                 "tenant_id": tenant3.id,
                "server_id": "3"})
    server_3 = servers.Server(servers.ServerManager(None),
                              json.loads(SERVER_DATA % vals)['server'])
    vals.update({"name": "server_4",
                 "status": "PAUSED",
                 "server_id": "4"})
    server_4 = servers.Server(servers.ServerManager(None),
                              json.loads(SERVER_DATA % vals)['server'])
    TEST.servers.add(server_1, server_2, server_3, server_4)

    # VNC Console Data
    console = {u'console': {u'url': u'http://example.com:6080/vnc_auto.html',
                            u'type': u'novnc'}}
    TEST.servers.vnc_console_data = console
    # SPICE Console Data
    console = {u'console': {u'url': u'http://example.com:6080/spice_auto.html',
                            u'type': u'spice'}}
    TEST.servers.spice_console_data = console
    # RDP Console Data
    console = {u'console': {u'url': u'http://example.com:6080/rdp_auto.html',
                            u'type': u'rdp'}}
    TEST.servers.rdp_console_data = console

    # Floating IPs
    def generate_fip(conf):
        return floating_ips.FloatingIP(floating_ips.FloatingIPManager(None),
                                       conf)

    fip_1 = {'id': 1,
             'fixed_ip': '10.0.0.4',
             'instance_id': server_1.id,
             'ip': '58.58.58.58',
             'pool': 'pool1'}
    fip_2 = {'id': 2,
             'fixed_ip': None,
             'instance_id': None,
             'ip': '58.58.58.58',
             'pool': 'pool2'}
    # this floating ip is for lbaas tests
    fip_3 = {'id': 3,
             'fixed_ip': '10.0.0.5',
             # the underlying class maps the instance id to port id
             'instance_id': '063cf7f3-ded1-4297-bc4c-31eae876cc91',
             'ip': '58.58.58.58',
             'pool': 'pool2'}
    TEST.api_floating_ips.add(generate_fip(fip_1), generate_fip(fip_2),
                              generate_fip(fip_3))

    TEST.floating_ips.add(nova.FloatingIp(generate_fip(fip_1)),
                          nova.FloatingIp(generate_fip(fip_2)),
                          nova.FloatingIp(generate_fip(fip_3)))

    # Floating IP with UUID id (for Floating IP with Neutron Proxy)
    fip_3 = {'id': str(uuid.uuid4()),
             'fixed_ip': '10.0.0.4',
             'instance_id': server_1.id,
             'ip': '58.58.58.58',
             'pool': 'pool1'}
    fip_4 = {'id': str(uuid.uuid4()),
             'fixed_ip': None,
             'instance_id': None,
             'ip': '58.58.58.58',
             'pool': 'pool2'}
    TEST.api_floating_ips_uuid.add(generate_fip(fip_3), generate_fip(fip_4))

    TEST.floating_ips_uuid.add(nova.FloatingIp(generate_fip(fip_3)),
                               nova.FloatingIp(generate_fip(fip_4)))

    # Usage
    usage_vals = {"tenant_id": TEST.tenant.id,
                  "instance_name": server_1.name,
                  "flavor_name": flavor_1.name,
                  "flavor_vcpus": flavor_1.vcpus,
                  "flavor_disk": flavor_1.disk,
                  "flavor_ram": flavor_1.ram}
    usage_obj = usage.Usage(usage.UsageManager(None),
                            json.loads(USAGE_DATA % usage_vals))
    TEST.usages.add(usage_obj)

    usage_2_vals = {"tenant_id": tenant3.id,
                    "instance_name": server_3.name,
                    "flavor_name": flavor_1.name,
                    "flavor_vcpus": flavor_1.vcpus,
                    "flavor_disk": flavor_1.disk,
                    "flavor_ram": flavor_1.ram}
    usage_obj_2 = usage.Usage(usage.UsageManager(None),
                              json.loads(USAGE_DATA % usage_2_vals))
    TEST.usages.add(usage_obj_2)

    volume_snapshot = vol_snaps.Snapshot(
        vol_snaps.SnapshotManager(None),
        {'id': '40f3fabf-3613-4f5e-90e5-6c9a08333fc3',
         'display_name': 'test snapshot',
         'display_description': 'vol snap!',
         'size': 40,
         'status': 'available',
         'volume_id': '41023e92-8008-4c8b-8059-7f2293ff3775'})
    volume_snapshot2 = vol_snaps.Snapshot(
        vol_snaps.SnapshotManager(None),
        {'id': 'a374cbb8-3f99-4c3f-a2ef-3edbec842e31',
         'display_name': '',
         'display_description': 'vol snap 2!',
         'size': 80,
         'status': 'available',
         'volume_id': '3b189ac8-9166-ac7f-90c9-16c8bf9e01ac'})
    TEST.volume_snapshots.add(volume_snapshot)
    TEST.volume_snapshots.add(volume_snapshot2)

    cert_data = {'private_key': 'private',
                 'data': 'certificate_data'}
    certificate = certs.Certificate(certs.CertificateManager(None), cert_data)
    TEST.certs.add(certificate)

    # Availability Zones
    TEST.availability_zones.add(availability_zones.AvailabilityZone(
        availability_zones.AvailabilityZoneManager(None),
        {
            'zoneName': 'nova',
            'zoneState': {'available': True},
            'hosts': {
                "host001": {
                    "nova-network": {
                        "active": True,
                        "available": True,
                    },
                },
            },
        },
    ))

    # hypervisors
    hypervisor_1 = hypervisors.Hypervisor(
        hypervisors.HypervisorManager(None),
        {
            "service": {"host": "devstack001", "id": 3},
            "vcpus_used": 1,
            "hypervisor_type": "QEMU",
            "local_gb_used": 20,
            "hypervisor_hostname": "devstack001",
            "memory_mb_used": 1500,
            "memory_mb": 2000,
            "current_workload": 0,
            "vcpus": 1,
            "cpu_info": '{"vendor": "Intel", "model": "core2duo",'
                        '"arch": "x86_64", "features": ["lahf_lm"'
                        ', "rdtscp"], "topology": {"cores": 1, "t'
                        'hreads": 1, "sockets": 1}}',
            "running_vms": 1,
            "free_disk_gb": 9,
            "hypervisor_version": 1002000,
            "disk_available_least": 6,
            "local_gb": 29,
            "free_ram_mb": 500,
            "id": 1,
            "servers": [{"name": "test_name", "uuid": "test_uuid"}]
        },
    )

    hypervisor_2 = hypervisors.Hypervisor(
        hypervisors.HypervisorManager(None),
        {
            "service": {"host": "devstack002", "id": 4},
            "vcpus_used": 1,
            "hypervisor_type": "QEMU",
            "local_gb_used": 20,
            "hypervisor_hostname": "devstack001",
            "memory_mb_used": 1500,
            "memory_mb": 2000,
            "current_workload": 0,
            "vcpus": 1,
            "cpu_info": '{"vendor": "Intel", "model": "core2duo",'
                        '"arch": "x86_64", "features": ["lahf_lm"'
                        ', "rdtscp"], "topology": {"cores": 1, "t'
                        'hreads": 1, "sockets": 1}}',
            "running_vms": 1,
            "free_disk_gb": 9,
            "hypervisor_version": 1002000,
            "disk_available_least": 6,
            "local_gb": 29,
            "free_ram_mb": 500,
            "id": 2,
            "servers": [{"name": "test_name_2", "uuid": "test_uuid_2"}]
        },
    )
    hypervisor_3 = hypervisors.Hypervisor(
        hypervisors.HypervisorManager(None),
        {
            "service": {"host": "instance-host", "id": 5},
            "vcpus_used": 1,
            "hypervisor_type": "QEMU",
            "local_gb_used": 20,
            "hypervisor_hostname": "devstack003",
            "memory_mb_used": 1500,
            "memory_mb": 2000,
            "current_workload": 0,
            "vcpus": 1,
            "cpu_info": '{"vendor": "Intel", "model": "core2duo",'
                        '"arch": "x86_64", "features": ["lahf_lm"'
                        ', "rdtscp"], "topology": {"cores": 1, "t'
                        'hreads": 1, "sockets": 1}}',
            "running_vms": 1,
            "free_disk_gb": 9,
            "hypervisor_version": 1002000,
            "disk_available_least": 6,
            "local_gb": 29,
            "free_ram_mb": 500,
            "id": 3,
        },
    )
    TEST.hypervisors.add(hypervisor_1)
    TEST.hypervisors.add(hypervisor_2)
    TEST.hypervisors.add(hypervisor_3)

    TEST.hypervisors.stats = {
        "hypervisor_statistics": {
            "count": 5,
            "vcpus_used": 3,
            "local_gb_used": 15,
            "memory_mb": 483310,
            "current_workload": 0,
            "vcpus": 160,
            "running_vms": 3,
            "free_disk_gb": 12548,
            "disk_available_least": 12556,
            "local_gb": 12563,
            "free_ram_mb": 428014,
            "memory_mb_used": 55296,
        }
    }

    # Services
    service_1 = services.Service(services.ServiceManager(None), {
        "status": "enabled",
        "binary": "nova-conductor",
        "zone": "internal",
        "state": "up",
        "updated_at": "2013-07-08T05:21:00.000000",
        "host": "devstack001",
        "disabled_reason": None,
    })

    service_2 = services.Service(services.ServiceManager(None), {
        "status": "enabled",
        "binary": "nova-compute",
        "zone": "nova",
        "state": "up",
        "updated_at": "2013-07-08T05:20:51.000000",
        "host": "devstack001",
        "disabled_reason": None,
    })

    service_3 = services.Service(services.ServiceManager(None), {
        "status": "enabled",
        "binary": "nova-compute",
        "zone": "nova",
        "state": "down",
        "updated_at": "2013-07-08T04:20:51.000000",
        "host": "devstack002",
        "disabled_reason": None,
    })

    service_4 = services.Service(services.ServiceManager(None), {
        "status": "disabled",
        "binary": "nova-compute",
        "zone": "nova",
        "state": "up",
        "updated_at": "2013-07-08T04:20:51.000000",
        "host": "devstack003",
        "disabled_reason": None,
    })

    TEST.services.add(service_1)
    TEST.services.add(service_2)
    TEST.services.add(service_3)
    TEST.services.add(service_4)

    # Aggregates
    aggregate_1 = aggregates.Aggregate(aggregates.AggregateManager(None), {
        "name": "foo",
        "availability_zone": "testing",
        "deleted": 0,
        "created_at": "2013-07-04T13:34:38.000000",
        "updated_at": None,
        "hosts": ["foo", "bar"],
        "deleted_at": None,
        "id": 1,
        "metadata": {"foo": "testing", "bar": "testing"},
    })

    aggregate_2 = aggregates.Aggregate(aggregates.AggregateManager(None), {
        "name": "bar",
        "availability_zone": "testing",
        "deleted": 0,
        "created_at": "2013-07-04T13:34:38.000000",
        "updated_at": None,
        "hosts": ["foo", "bar"],
        "deleted_at": None,
        "id": 2,
        "metadata": {"foo": "testing", "bar": "testing"},
    })

    TEST.aggregates.add(aggregate_1)
    TEST.aggregates.add(aggregate_2)

    host1 = hosts.Host(hosts.HostManager(None), {
        "host_name": "devstack001",
        "service": "compute",
        "zone": "testing",
    })

    host2 = hosts.Host(hosts.HostManager(None), {
        "host_name": "devstack002",
        "service": "nova-conductor",
        "zone": "testing",
    })

    host3 = hosts.Host(hosts.HostManager(None), {
        "host_name": "devstack003",
        "service": "compute",
        "zone": "testing",
    })

    host4 = hosts.Host(hosts.HostManager(None), {
        "host_name": "devstack004",
        "service": "compute",
        "zone": "testing",
    })

    TEST.hosts.add(host1)
    TEST.hosts.add(host2)
    TEST.hosts.add(host3)
    TEST.hosts.add(host4)
