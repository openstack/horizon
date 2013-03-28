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

import copy
import json
import uuid

from novaclient.v1_1 import (flavors, keypairs, servers, volumes,
                             volume_types, quotas,
                             floating_ips, usage, certs,
                             volume_snapshots as vol_snaps,
                             security_group_rules as rules,
                             security_groups as sec_groups)

from openstack_dashboard.api.base import Quota, QuotaSet as QuotaSetWrapper
from openstack_dashboard.api.nova import FloatingIp as NetFloatingIp
from openstack_dashboard.usage.quotas import QuotaUsage
from .utils import TestDataContainer


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
    TEST.servers = TestDataContainer()
    TEST.flavors = TestDataContainer()
    TEST.keypairs = TestDataContainer()
    TEST.security_groups = TestDataContainer()
    TEST.security_groups_uuid = TestDataContainer()
    TEST.security_group_rules = TestDataContainer()
    TEST.security_group_rules_uuid = TestDataContainer()
    TEST.volumes = TestDataContainer()
    TEST.quotas = TestDataContainer()
    TEST.quota_usages = TestDataContainer()
    TEST.floating_ips = TestDataContainer()
    TEST.floating_ips_uuid = TestDataContainer()
    TEST.usages = TestDataContainer()
    TEST.certs = TestDataContainer()
    TEST.volume_snapshots = TestDataContainer()
    TEST.volume_types = TestDataContainer()

    # Data return by novaclient.
    # It is used if API layer does data conversion.
    TEST.api_floating_ips = TestDataContainer()
    TEST.api_floating_ips_uuid = TestDataContainer()

    # Volumes
    volume = volumes.Volume(volumes.VolumeManager(None),
                            dict(id="41023e92-8008-4c8b-8059-7f2293ff3775",
                                 name='test_volume',
                                 status='available',
                                 size=40,
                                 display_name='Volume name',
                                 created_at='2012-04-01 10:30:00',
                                 volume_type=None,
                                 attachments=[]))
    nameless_volume = volumes.Volume(volumes.VolumeManager(None),
                         dict(id="3b189ac8-9166-ac7f-90c9-16c8bf9e01ac",
                              name='',
                              status='in-use',
                              size=10,
                              display_name='',
                              display_description='',
                              device="/dev/hda",
                              created_at='2010-11-21 18:34:25',
                              volume_type='vol_type_1',
                              attachments=[{"id": "1", "server_id": '1',
                                            "device": "/dev/hda"}]))
    attached_volume = volumes.Volume(volumes.VolumeManager(None),
                         dict(id="8cba67c1-2741-6c79-5ab6-9c2bf8c96ab0",
                              name='my_volume',
                              status='in-use',
                              size=30,
                              display_name='My Volume',
                              display_description='',
                              device="/dev/hdk",
                              created_at='2011-05-01 11:54:33',
                              volume_type='vol_type_2',
                              attachments=[{"id": "2", "server_id": '1',
                                            "device": "/dev/hdk"}]))
    TEST.volumes.add(volume)
    TEST.volumes.add(nameless_volume)
    TEST.volumes.add(attached_volume)

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
                               'extra_specs': {},
                               'OS-FLV-EXT-DATA:ephemeral': 0})
    flavor_2 = flavors.Flavor(flavors.FlavorManager(None),
                              {'id': "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                               'name': 'm1.massive',
                               'vcpus': 1000,
                               'disk': 1024,
                               'ram': 10000,
                               'swap': 0,
                               'extra_specs': {'Trusted': True, 'foo': 'bar'},
                               'OS-FLV-EXT-DATA:ephemeral': 2048})
    TEST.flavors.add(flavor_1, flavor_2)

    # Keypairs
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
                'ip_protocol': u"tcp",
                'from_port': u"80",
                'to_port': u"80",
                'parent_group_id': sec_group_1.id,
                'ip_range': {'cidr': u"0.0.0.0/32"}}

        icmp_rule = {'id': get_id(is_uuid),
                     'ip_protocol': u"icmp",
                     'from_port': u"9",
                     'to_port': u"5",
                     'parent_group_id': sec_group_1.id,
                     'ip_range': {'cidr': u"0.0.0.0/32"}}

        group_rule = {'id': 3,
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
                      volumes='1',
                      gigabytes='1000',
                      ram=10000,
                      floating_ips='1',
                      fixed_ips='10',
                      instances='10',
                      injected_files='1',
                      cores='10',
                      security_groups='10',
                      security_group_rules='20')
    quota = quotas.QuotaSet(quotas.QuotaSetManager(None), quota_data)
    TEST.quotas.nova = QuotaSetWrapper(quota)
    TEST.quotas.add(QuotaSetWrapper(quota))

    # Quota Usages
    quota_usage_data = {'gigabytes': {'used': 0,
                                      'quota': 1000},
                        'instances': {'used': 0,
                                      'quota': 10},
                        'ram': {'used': 0,
                                'quota': 10000},
                        'cores': {'used': 0,
                                  'quota': 20}}
    quota_usage = QuotaUsage()
    for k, v in quota_usage_data.items():
        quota_usage.add_quota(Quota(k, v['quota']))
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
    TEST.servers.add(server_1, server_2)

    # VNC Console Data
    console = {u'console': {u'url': u'http://example.com:6080/vnc_auto.html',
                            u'type': u'novnc'}}
    TEST.servers.vnc_console_data = console
    # SPICE Console Data
    console = {u'console': {u'url': u'http://example.com:6080/spice_auto.html',
                            u'type': u'spice'}}
    TEST.servers.spice_console_data = console
    # Floating IPs
    fip_1 = floating_ips.FloatingIP(floating_ips.FloatingIPManager(None),
                                    {'id': 1,
                                     'fixed_ip': '10.0.0.4',
                                     'instance_id': server_1.id,
                                     'ip': '58.58.58.58',
                                     'pool': 'pool1'})
    fip_2 = floating_ips.FloatingIP(floating_ips.FloatingIPManager(None),
                                    {'id': 2,
                                     'fixed_ip': None,
                                     'instance_id': None,
                                     'ip': '58.58.58.58',
                                     'pool': 'pool2'})
    TEST.api_floating_ips.add(fip_1, fip_2)

    TEST.floating_ips.add(NetFloatingIp(copy.deepcopy(fip_1)),
                          NetFloatingIp(copy.deepcopy(fip_2)))

    # Floating IP with UUID id (for Floating IP with Quantum Proxy)
    fip_3 = floating_ips.FloatingIP(floating_ips.FloatingIPManager(None),
                                    {'id': str(uuid.uuid4()),
                                     'fixed_ip': '10.0.0.4',
                                     'instance_id': server_1.id,
                                     'ip': '58.58.58.58',
                                     'pool': 'pool1'})
    fip_4 = floating_ips.FloatingIP(floating_ips.FloatingIPManager(None),
                                    {'id': str(uuid.uuid4()),
                                     'fixed_ip': None,
                                     'instance_id': None,
                                     'ip': '58.58.58.58',
                                     'pool': 'pool2'})
    TEST.api_floating_ips_uuid.add(fip_3, fip_4)

    TEST.floating_ips_uuid.add(NetFloatingIp(copy.deepcopy(fip_3)),
                               NetFloatingIp(copy.deepcopy(fip_4)))

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

    volume_snapshot = vol_snaps.Snapshot(vol_snaps.SnapshotManager(None),
                        {'id': '40f3fabf-3613-4f5e-90e5-6c9a08333fc3',
                         'display_name': 'test snapshot',
                         'display_description': 'vol snap!',
                         'size': 40,
                         'status': 'available',
                         'volume_id': '41023e92-8008-4c8b-8059-7f2293ff3775'})
    TEST.volume_snapshots.add(volume_snapshot)

    cert_data = {'private_key': 'private',
                 'data': 'certificate_data'}
    certificate = certs.Certificate(certs.CertificateManager(None), cert_data)
    TEST.certs.add(certificate)
