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

from cinderclient.v2 import availability_zones
from cinderclient.v2 import pools
from cinderclient.v2 import qos_specs
from cinderclient.v2 import quotas
from cinderclient.v2 import services
from cinderclient.v2 import volume_backups as vol_backups
from cinderclient.v2 import volume_encryption_types as vol_enc_types
from cinderclient.v2 import volume_snapshots as vol_snaps
from cinderclient.v2 import volume_transfers
from cinderclient.v2 import volume_types
from cinderclient.v2 import volumes

from openstack_dashboard import api
from openstack_dashboard.usage import quotas as usage_quotas

from openstack_dashboard.test.test_data import utils


def data(TEST):
    TEST.cinder_services = utils.TestDataContainer()
    TEST.cinder_volumes = utils.TestDataContainer()
    TEST.cinder_volume_backups = utils.TestDataContainer()
    TEST.cinder_volume_encryption_types = utils.TestDataContainer()
    TEST.cinder_volume_types = utils.TestDataContainer()
    TEST.cinder_volume_encryption = utils.TestDataContainer()
    TEST.cinder_bootable_volumes = utils.TestDataContainer()
    TEST.cinder_qos_specs = utils.TestDataContainer()
    TEST.cinder_qos_spec_associations = utils.TestDataContainer()
    TEST.cinder_volume_snapshots = utils.TestDataContainer()
    TEST.cinder_quotas = utils.TestDataContainer()
    TEST.cinder_quota_usages = utils.TestDataContainer()
    TEST.cinder_availability_zones = utils.TestDataContainer()
    TEST.cinder_volume_transfers = utils.TestDataContainer()
    TEST.cinder_pools = utils.TestDataContainer()

    # Services
    service_1 = services.Service(services.ServiceManager(None), {
        "service": "cinder-scheduler",
        "status": "enabled",
        "binary": "cinder-scheduler",
        "zone": "internal",
        "state": "up",
        "updated_at": "2013-07-08T05:21:00.000000",
        "host": "devstack001",
        "disabled_reason": None
    })

    service_2 = services.Service(services.ServiceManager(None), {
        "service": "cinder-volume",
        "status": "enabled",
        "binary": "cinder-volume",
        "zone": "nova",
        "state": "up",
        "updated_at": "2013-07-08T05:20:51.000000",
        "host": "devstack001",
        "disabled_reason": None
    })
    TEST.cinder_services.add(service_1)
    TEST.cinder_services.add(service_2)

    # Volumes - Cinder v1
    volume = volumes.Volume(
        volumes.VolumeManager(None),
        {'id': "11023e92-8008-4c8b-8059-7f2293ff3887",
         'status': 'available',
         'size': 40,
         'display_name': 'Volume name',
         'display_description': 'Volume description',
         'created_at': '2014-01-27 10:30:00',
         'volume_type': None,
         'attachments': []})
    nameless_volume = volumes.Volume(
        volumes.VolumeManager(None),
        {"id": "4b069dd0-6eaa-4272-8abc-5448a68f1cce",
         "status": 'available',
         "size": 10,
         "display_name": '',
         "display_description": '',
         "device": "/dev/hda",
         "created_at": '2010-11-21 18:34:25',
         "volume_type": 'vol_type_1',
         "attachments": []})
    other_volume = volumes.Volume(
        volumes.VolumeManager(None),
        {'id': "21023e92-8008-1234-8059-7f2293ff3889",
         'status': 'in-use',
         'size': 10,
         'display_name': u'my_volume',
         'display_description': '',
         'created_at': '2013-04-01 10:30:00',
         'volume_type': None,
         'attachments': [{"id": "1", "server_id": '1',
                          "device": "/dev/hda"}]})
    volume_with_type = volumes.Volume(
        volumes.VolumeManager(None),
        {'id': "7dcb47fd-07d9-42c2-9647-be5eab799ebe",
         'name': 'my_volume2',
         'status': 'in-use',
         'size': 10,
         'display_name': u'my_volume2',
         'display_description': '',
         'created_at': '2013-04-01 10:30:00',
         'volume_type': 'vol_type_2',
         'attachments': [{"id": "2", "server_id": '2',
                          "device": "/dev/hdb"}]})
    non_bootable_volume = volumes.Volume(
        volumes.VolumeManager(None),
        {'id': "21023e92-8008-1234-8059-7f2293ff3890",
         'status': 'in-use',
         'size': 10,
         'display_name': u'my_volume',
         'display_description': '',
         'created_at': '2013-04-01 10:30:00',
         'volume_type': None,
         'bootable': False,
         'attachments': [{"id": "1", "server_id": '1',
                          "device": "/dev/hda"}]})

    volume.bootable = 'true'
    nameless_volume.bootable = 'true'
    other_volume.bootable = 'true'

    TEST.cinder_volumes.add(api.cinder.Volume(volume))
    TEST.cinder_volumes.add(api.cinder.Volume(nameless_volume))
    TEST.cinder_volumes.add(api.cinder.Volume(other_volume))
    TEST.cinder_volumes.add(api.cinder.Volume(volume_with_type))

    TEST.cinder_bootable_volumes.add(api.cinder.Volume(non_bootable_volume))

    vol_type1 = volume_types.VolumeType(volume_types.VolumeTypeManager(None),
                                        {'id': u'1',
                                         'name': u'vol_type_1',
                                         'description': 'type 1 description',
                                         'extra_specs': {'foo': 'bar'}})
    vol_type2 = volume_types.VolumeType(volume_types.VolumeTypeManager(None),
                                        {'id': u'2',
                                         'name': u'vol_type_2',
                                         'description': 'type 2 description'})
    TEST.cinder_volume_types.add(vol_type1, vol_type2)

    # Volumes - Cinder v2
    volume_v2 = volumes.Volume(
        volumes.VolumeManager(None),
        {'id': "31023e92-8008-4c8b-8059-7f2293ff1234",
         'name': 'v2_volume',
         'description': "v2 Volume Description",
         'status': 'available',
         'size': 20,
         'created_at': '2014-01-27 10:30:00',
         'volume_type': None,
         'os-vol-host-attr:host': 'host@backend-name#pool',
         'bootable': 'true',
         'attachments': []})
    volume_v2.bootable = 'true'

    TEST.cinder_volumes.add(api.cinder.Volume(volume_v2))

    snapshot = vol_snaps.Snapshot(
        vol_snaps.SnapshotManager(None),
        {'id': '5f3d1c33-7d00-4511-99df-a2def31f3b5d',
         'display_name': 'test snapshot',
         'display_description': 'volume snapshot',
         'size': 40,
         'status': 'available',
         'volume_id': '11023e92-8008-4c8b-8059-7f2293ff3887'})
    snapshot2 = vol_snaps.Snapshot(
        vol_snaps.SnapshotManager(None),
        {'id': 'c9d0881a-4c0b-4158-a212-ad27e11c2b0f',
         'name': '',
         'description': 'v2 volume snapshot description',
         'size': 80,
         'status': 'available',
         'volume_id': '31023e92-8008-4c8b-8059-7f2293ff1234'})
    snapshot3 = vol_snaps.Snapshot(
        vol_snaps.SnapshotManager(None),
        {'id': 'c9d0881a-4c0b-4158-a212-ad27e11c2b0e',
         'name': '',
         'description': 'v2 volume snapshot description 2',
         'size': 80,
         'status': 'available',
         'volume_id': '31023e92-8008-4c8b-8059-7f2293ff1234'})

    snapshot.bootable = 'true'
    snapshot2.bootable = 'true'

    TEST.cinder_volume_snapshots.add(api.cinder.VolumeSnapshot(snapshot))
    TEST.cinder_volume_snapshots.add(api.cinder.VolumeSnapshot(snapshot2))
    TEST.cinder_volume_snapshots.add(api.cinder.VolumeSnapshot(snapshot3))
    TEST.cinder_volume_snapshots.first()._volume = volume

    # Volume Type Encryption
    vol_enc_type1 = vol_enc_types.VolumeEncryptionType(
        vol_enc_types.VolumeEncryptionTypeManager(None),
        {'volume_type_id': u'1',
         'control_location': "front-end",
         'key_size': 512,
         'provider': "a-provider",
         'cipher': "a-cipher"})
    vol_enc_type2 = vol_enc_types.VolumeEncryptionType(
        vol_enc_types.VolumeEncryptionTypeManager(None),
        {'volume_type_id': u'2',
         'control_location': "front-end",
         'key_size': 256,
         'provider': "a-provider",
         'cipher': "a-cipher"})
    vol_unenc_type1 = vol_enc_types.VolumeEncryptionType(
        vol_enc_types.VolumeEncryptionTypeManager(None), {})
    TEST.cinder_volume_encryption_types.add(vol_enc_type1, vol_enc_type2,
                                            vol_unenc_type1)

    volume_backup1 = vol_backups.VolumeBackup(
        vol_backups.VolumeBackupManager(None),
        {'id': 'a374cbb8-3f99-4c3f-a2ef-3edbec842e31',
         'name': 'backup1',
         'description': 'volume backup 1',
         'size': 10,
         'status': 'available',
         'container_name': 'volumebackups',
         'volume_id': '11023e92-8008-4c8b-8059-7f2293ff3887'})

    volume_backup2 = vol_backups.VolumeBackup(
        vol_backups.VolumeBackupManager(None),
        {'id': 'c321cbb8-3f99-4c3f-a2ef-3edbec842e52',
         'name': 'backup2',
         'description': 'volume backup 2',
         'size': 20,
         'status': 'available',
         'container_name': 'volumebackups',
         'volume_id': '31023e92-8008-4c8b-8059-7f2293ff1234'})

    volume_backup3 = vol_backups.VolumeBackup(
        vol_backups.VolumeBackupManager(None),
        {'id': 'c321cbb8-3f99-4c3f-a2ef-3edbec842e53',
         'name': 'backup3',
         'description': 'volume backup 3',
         'size': 20,
         'status': 'available',
         'container_name': 'volumebackups',
         'volume_id': '31023e92-8008-4c8b-8059-7f2293ff1234'})

    TEST.cinder_volume_backups.add(volume_backup1)
    TEST.cinder_volume_backups.add(volume_backup2)
    TEST.cinder_volume_backups.add(volume_backup3)

    # Volume Encryption
    vol_enc_metadata1 = volumes.Volume(
        volumes.VolumeManager(None),
        {'cipher': 'test-cipher',
         'key_size': 512,
         'provider': 'test-provider',
         'control_location': 'front-end'})
    vol_unenc_metadata1 = volumes.Volume(
        volumes.VolumeManager(None),
        {})
    TEST.cinder_volume_encryption.add(vol_enc_metadata1)
    TEST.cinder_volume_encryption.add(vol_unenc_metadata1)

    # Quota Sets
    quota_data = dict(volumes='1',
                      snapshots='1',
                      gigabytes='1000')
    quota = quotas.QuotaSet(quotas.QuotaSetManager(None), quota_data)
    TEST.cinder_quotas.add(api.base.QuotaSet(quota))

    # Quota Usages
    quota_usage_data = {'gigabytes': {'used': 0,
                                      'quota': 1000},
                        'instances': {'used': 0,
                                      'quota': 10},
                        'snapshots': {'used': 0,
                                      'quota': 10}}
    quota_usage = usage_quotas.QuotaUsage()
    for k, v in quota_usage_data.items():
        quota_usage.add_quota(api.base.Quota(k, v['quota']))
        quota_usage.tally(k, v['used'])

    TEST.cinder_quota_usages.add(quota_usage)

    # Availability Zones
    # Cinder returns the following structure from os-availability-zone
    # {"availabilityZoneInfo":
    # [{"zoneState": {"available": true}, "zoneName": "nova"}]}
    # Note that the default zone is still "nova" even though this is cinder
    TEST.cinder_availability_zones.add(
        availability_zones.AvailabilityZone(
            availability_zones.AvailabilityZoneManager(None),
            {
                'zoneName': 'nova',
                'zoneState': {'available': True}
            }
        )
    )
    # Cinder Limits
    limits = {"absolute": {"totalVolumesUsed": 1,
                           "totalGigabytesUsed": 5,
                           "maxTotalVolumeGigabytes": 1000,
                           "maxTotalVolumes": 10}}
    TEST.cinder_limits = limits

    # QOS Specs
    qos_spec1 = qos_specs.QoSSpecs(
        qos_specs.QoSSpecsManager(None),
        {"id": "418db45d-6992-4674-b226-80aacad2073c",
         "name": "high_iops",
         "consumer": "back-end",
         "specs": {"minIOPS": "1000", "maxIOPS": '100000'}})
    qos_spec2 = qos_specs.QoSSpecs(
        qos_specs.QoSSpecsManager(None),
        {"id": "6ed7035f-992e-4075-8ed6-6eff19b3192d",
         "name": "high_bws",
         "consumer": "back-end",
         "specs": {"maxBWS": '5000'}})

    TEST.cinder_qos_specs.add(qos_spec1, qos_spec2)
    vol_type1.associated_qos_spec = qos_spec1.name
    TEST.cinder_qos_spec_associations.add(vol_type1)

    # volume_transfers
    transfer_1 = volume_transfers.VolumeTransfer(
        volume_transfers.VolumeTransferManager(None), {
            'id': '99999999-8888-7777-6666-555555555555',
            'name': 'test transfer',
            'volume_id': volume.id,
            'auth_key': 'blah',
            'created_at': ''})
    TEST.cinder_volume_transfers.add(transfer_1)

    # Pools
    pool1 = pools.Pool(
        pools.PoolManager(None), {
            "QoS_support": False,
            "allocated_capacity_gb": 0,
            "driver_version": "3.0.0",
            "free_capacity_gb": 10,
            "extra_specs": {
                "description": "LVM Extra specs",
                "display_name": "LVMDriver",
                "namespace": "OS::Cinder::LVMDriver",
                "type": "object",
            },
            "name": "devstack@lvmdriver-1#lvmdriver-1",
            "pool_name": "lvmdriver-1",
            "reserved_percentage": 0,
            "storage_protocol": "iSCSI",
            "total_capacity_gb": 10,
            "vendor_name": "Open Source",
            "volume_backend_name": "lvmdriver-1"})

    pool2 = pools.Pool(
        pools.PoolManager(None), {
            "QoS_support": False,
            "allocated_capacity_gb": 2,
            "driver_version": "3.0.0",
            "free_capacity_gb": 15,
            "extra_specs": {
                "description": "LVM Extra specs",
                "display_name": "LVMDriver",
                "namespace": "OS::Cinder::LVMDriver",
                "type": "object",
            },
            "name": "devstack@lvmdriver-2#lvmdriver-2",
            "pool_name": "lvmdriver-2",
            "reserved_percentage": 0,
            "storage_protocol": "iSCSI",
            "total_capacity_gb": 10,
            "vendor_name": "Open Source",
            "volume_backend_name": "lvmdriver-2"})

    TEST.cinder_pools.add(pool1)
    TEST.cinder_pools.add(pool2)
