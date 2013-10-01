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

from django.conf import settings  # noqa

try:
    from troveclient import auth
    from troveclient import client
    with_trove = True
except ImportError:
    with_trove = False


class TokenAuth(object):
    """Simple Token Authentication handler for trove api"""

    def __init__(self, client, auth_strategy, auth_url, username, password,
                 tenant, region, service_type, service_name, service_url):
        # TODO(rmyers): handle some of these other args
        self.username = username
        self.service_type = service_type
        self.service_name = service_name
        self.region = region

    def authenticate(self):
        catalog = {
            'access': {
                'serviceCatalog': self.username.service_catalog,
                'token': {
                    'id': self.username.token.id,
                }
            }
        }
        if not with_trove:
            return None
        return auth.ServiceCatalog(catalog,
                                   service_type=self.service_type,
                                   service_name=self.service_name,
                                   region=self.region)


def troveclient(request):
    if not with_trove:
        return None
    return client.Dbaas(username=request.user,
                        api_key=None,
                        auth_strategy=TokenAuth,
                        region_name=request.user.services_region)


def instance_list(request, marker=None):
    default_page_size = getattr(settings, 'API_RESULT_PAGE_SIZE', 20)
    page_size = request.session.get('horizon_pagesize', default_page_size)
    return troveclient(request).instances.list(limit=page_size, marker=marker)


def instance_get(request, instance_id):
    return troveclient(request).instances.get(instance_id)


def instance_delete(request, instance_id):
    return troveclient(request).instances.delete(instance_id)


def instance_create(request, name, volume, flavor, databases=None,
                    users=None, restore_point=None):
    #TODO(dklyle): adding conditional to support trove without volume
    # support for now until API supports checking for volume support
    if volume > 0:
        volume_params = {'size': volume}
    else:
        volume_params = None
    return troveclient(request).instances.create(
        name,
        flavor,
        volume=volume_params,
        databases=databases,
        users=users,
        restorePoint=restore_point)


def instance_backups(request, instance_id):
    return troveclient(request).instances.backups(instance_id)


def instance_restart(request, instance_id):
    return troveclient(request).instances.restart(instance_id)


def database_list(request, instance_id):
    return troveclient(request).databases.list(instance_id)


def database_delete(request, instance_id, db_name):
    return troveclient(request).databases.delete(instance_id, db_name)


def backup_list(request):
    return troveclient(request).backups.list()


def backup_get(request, backup_id):
    return troveclient(request).backups.get(backup_id)


def backup_delete(request, backup_id):
    return troveclient(request).backups.delete(backup_id)


def backup_create(request, name, instance_id, description=None):
    return troveclient(request).backups.create(name, instance_id, description)


def flavor_list(request):
    return troveclient(request).flavors.list()


def flavor_get(request, flavor_id):
    return troveclient(request).flavors.get(flavor_id)


def users_list(request, instance_id):
    return troveclient(request).users.list(instance_id)


def user_delete(request, instance_id, user):
    return troveclient(request).users.delete(instance_id, user)


def user_list_access(request, instance_id, user):
    return troveclient(request).users.list_access(instance_id, user)
