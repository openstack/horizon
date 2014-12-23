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

from troveclient.v1 import backups
from troveclient.v1 import databases
from troveclient.v1 import datastores
from troveclient.v1 import flavors
from troveclient.v1 import instances
from troveclient.v1 import users

from openstack_dashboard.test.test_data import utils


DATABASE_DATA_ONE = {
    "status": "ACTIVE",
    "updated": "2013-08-12T22:00:09",
    "name": "Test Database",
    "links": [],
    "created": "2013-08-12T22:00:03",
    "ip": [
        "10.0.0.3",
    ],
    "volume": {
        "used": 0.13,
        "size": 1,
    },
    "flavor": {
        "id": "1",
        "links": [],
    },
    "datastore": {
        "type": "mysql",
        "version": "5.5"
    },
    "id": "6ddc36d9-73db-4e23-b52e-368937d72719",
}

DATABASE_DATA_TWO = {
    "status": "ACTIVE",
    "updated": "2013-08-12T22:00:09",
    "name": "Test Database With DNS",
    "links": [],
    "created": "2013-08-12T22:00:03",
    "hostname": "trove.instance-2.com",
    "volume": {
        "used": 0.13,
        "size": 1,
    },
    "flavor": {
        "id": "1",
        "links": [],
    },
    "datastore": {
        "type": "mysql",
        "version": "5.6"
    },
    "id": "4d7b3f57-44f5-41d2-8e86-36b88cad572a",
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
    "description": "Long description of backup",
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
    "description": "Longer description of backup",
}


BACKUP_TWO_INC = {
    "instance_id": "4d7b3f57-44f5-41d2-8e86-36b88cad572a",
    "status": "COMPLETED",
    "updated": "2013-08-10T20:20:55",
    "locationRef": "http://swift/v1/AUTH/database_backups/f145.tar.gz",
    "name": "backup2-Incr",
    "created": "2013-08-10T20:20:37",
    "size": 0.13,
    "id": "e4602a3c-2bca-478f-b059-b6c215510fb5",
    "description": "Longer description of backup",
    "parent_id": "e4602a3c-2bca-478f-b059-b6c215510fb4",
}

USER_ONE = {
    "name": "Test_User",
    "host": "%",
    "databases": [DATABASE_DATA_ONE["name"]],
}


USER_DB_ONE = {
    "name": "db1",
}

DATASTORE_ONE = {
    "id": "537fb940-b5eb-40d9-bdbd-91a3dcb9c17d",
    "links": [],
    "name": "mysql"
}

DATASTORE_TWO = {
    "id": "ccb31517-c472-409d-89b4-1a13db6bdd36",
    "links": [],
    "name": "mysql"
}

VERSION_ONE = {
    "name": "5.5",
    "links": [],
    "image": "b7956bb5-920e-4299-b68e-2347d830d939",
    "active": 1,
    "datastore": "537fb940-b5eb-40d9-bdbd-91a3dcb9c17d",
    "packages": "5.5",
    "id": "390a6d52-8347-4e00-8e4c-f4fa9cf96ae9"
}

VERSION_TWO = {
    "name": "5.6",
    "links": [],
    "image": "c7956bb5-920e-4299-b68e-2347d830d938",
    "active": 1,
    "datastore": "537fb940-b5eb-40d9-bdbd-91a3dcb9c17d",
    "packages": "5.6",
    "id": "500a6d52-8347-4e00-8e4c-f4fa9cf96ae9"
}

FLAVOR_ONE = {
    "ram": 512,
    "id": "1",
    "links": [],
    "name": "m1.tiny"
}

FLAVOR_TWO = {
    "ram": 768,
    "id": "10",
    "links": [],
    "name": "eph.rd-smaller"
}

FLAVOR_THREE = {
    "ram": 800,
    "id": "100",
    "links": [],
    "name": "test.1"
}


def data(TEST):
    database1 = instances.Instance(instances.Instances(None),
                                   DATABASE_DATA_ONE)
    database2 = instances.Instance(instances.Instances(None),
                                   DATABASE_DATA_TWO)
    bkup1 = backups.Backup(backups.Backups(None), BACKUP_ONE)
    bkup2 = backups.Backup(backups.Backups(None), BACKUP_TWO)
    bkup3 = backups.Backup(backups.Backups(None), BACKUP_TWO_INC)
    user1 = users.User(users.Users(None), USER_ONE)
    user_db1 = databases.Database(databases.Databases(None),
                                  USER_DB_ONE)

    datastore1 = datastores.Datastore(datastores.Datastores(None),
                                      DATASTORE_ONE)

    version1 = datastores.\
        DatastoreVersion(datastores.DatastoreVersions(None),
                         VERSION_ONE)
    version2 = datastores.\
        DatastoreVersion(datastores.DatastoreVersions(None),
                         VERSION_TWO)

    flavor1 = flavors.Flavor(flavors.Flavors(None), FLAVOR_ONE)
    flavor2 = flavors.Flavor(flavors.Flavors(None), FLAVOR_TWO)
    flavor3 = flavors.Flavor(flavors.Flavors(None), FLAVOR_THREE)

    TEST.databases = utils.TestDataContainer()
    TEST.database_backups = utils.TestDataContainer()
    TEST.database_users = utils.TestDataContainer()
    TEST.database_user_dbs = utils.TestDataContainer()
    TEST.database_flavors = utils.TestDataContainer()

    TEST.databases.add(database1)
    TEST.databases.add(database2)
    TEST.database_backups.add(bkup1)
    TEST.database_backups.add(bkup2)
    TEST.database_backups.add(bkup3)
    TEST.database_users.add(user1)
    TEST.database_user_dbs.add(user_db1)
    TEST.datastores = utils.TestDataContainer()
    TEST.datastores.add(datastore1)
    TEST.datastore_versions = utils.TestDataContainer()
    TEST.datastore_versions.add(version1)
    TEST.datastore_versions.add(version2)
    TEST.database_flavors.add(flavor1, flavor2, flavor3)
