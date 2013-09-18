# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Rackspace Hosting.
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

try:
    from troveclient import backups
    from troveclient import instances
    with_trove = True
except ImportError:
    with_trove = False

from openstack_dashboard.test.test_data import utils


DATABASE_DATA = {
    "status": "ACTIVE",
    "updated": "2013-08-12T22:00:09",
    "name": "Test Database",
    "links": [],
    "created": "2013-08-12T22:00:03",
    "ip": [
        "10.0.0.3"
    ],
    "volume": {
        "used": 0.13,
        "size": 1
    },
    "flavor": {
        "id": "1",
        "links": []
    },
    "id": "6ddc36d9-73db-4e23-b52e-368937d72719"
}


BACKUP_ONE = {
    "instance_id": "6ddc36d9-73db-4e23-b52e-368937d72719",
    "status": "COMPLETED",
    "updated": "2013-08-13T19:39:38",
    "locationRef": "http://swift/v1/AUTH/database_backups/0edb.tar.gz",
    "name": "backup1",
    "created": "2013-08-15T18:10:14",
    "size": 0.13,
    "id": "0edb3c14-8919-4583-9add-00df9e524081",
    "description": "Long description of backup"
}


BACKUP_TWO = {
    "instance_id": "4d7b3f57-44f5-41d2-8e86-36b88cad572a",
    "status": "COMPLETED",
    "updated": "2013-08-10T20:20:44",
    "locationRef": "http://swift/v1/AUTH/database_backups/e460.tar.gz",
    "name": "backup2",
    "created": "2013-08-10T20:20:37",
    "size": 0.13,
    "id": "e4602a3c-2bca-478f-b059-b6c215510fb4",
    "description": "Longer description of backup"
}

if with_trove:
    def data(TEST):
        database = instances.Instance(instances.Instances(None), DATABASE_DATA)
        bkup1 = backups.Backup(backups.Backups(None), BACKUP_ONE)
        bkup2 = backups.Backup(backups.Backups(None), BACKUP_TWO)

        TEST.databases = utils.TestDataContainer()
        TEST.database_backups = utils.TestDataContainer()
        TEST.databases.add(database)
        TEST.database_backups.add(bkup1)
        TEST.database_backups.add(bkup2)
