# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Fourth Paradigm Development, Inc.
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

"""
Methods and interface objects used to interact with external apis.

API method calls return objects that are in many cases objects with
attributes that are direct maps to the data returned from the API http call.
Unfortunately, these objects are also often constructed dynamically, making
it difficult to know what data is available from the API object.  Because of
this, all API calls should wrap their returned object in one defined here,
using only explicitly defined atributes and/or methods.

In other words, django_openstack developers not working on django_openstack.api
shouldn't need to understand the finer details of APIs for Nova/Glance/Swift et
al.
"""

from django.conf import settings

import cloudfiles
import glance.client
import httplib
import json
import logging
import openstack.compute
import openstackx.admin
import openstackx.extras
import openstackx.auth
from urlparse import urlparse


LOG = logging.getLogger('django_openstack.api')


class APIResourceWrapper(object):
    ''' Simple wrapper for api objects

        Define _attrs on the child class and pass in the
        api object as the only argument to the constructor
    '''
    _attrs = []

    def __init__(self, apiresource):
        self._apiresource = apiresource

    def __getattr__(self, attr):
        if attr in self._attrs:
            # __getattr__ won't find properties
            return self._apiresource.__getattribute__(attr)
        else:
            LOG.debug('Attempted to access unknown attribute "%s" on'
                      ' APIResource object of type "%s" wrapping resource of'
                      ' type "%s"' % (attr, self.__class__,
                                      self._apiresource.__class__))
            raise AttributeError(attr)


class APIDictWrapper(object):
    ''' Simple wrapper for api dictionaries

        Some api calls return dictionaries.  This class provides identical
        behavior as APIResourceWrapper, except that it will also behave as a
        dictionary, in addition to attribute accesses.

        Attribute access is the preferred method of access, to be
        consistent with api resource objects from openstackx
    '''
    def __init__(self, apidict):
        self._apidict = apidict

    def __getattr__(self, attr):
        if attr in self._attrs:
            try:
                return self._apidict[attr]
            except KeyError, e:
                raise AttributeError(e)

        else:
            LOG.debug('Attempted to access unknown item "%s" on'
                      'APIResource object of type "%s"'
                      % (attr, self.__class__))
            raise AttributeError(attr)

    def __getitem__(self, item):
        try:
            return self.__getattr__(item)
        except AttributeError, e:
            # caller is expecting a KeyError
            raise KeyError(e)

    def get(self, item, default=None):
        try:
            return self.__getattr__(item)
        except AttributeError:
            return default


class Container(APIResourceWrapper):
    '''Simple wrapper around cloudfiles.container.Container'''
    _attrs = ['name']


class Console(APIResourceWrapper):
    '''Simple wrapper around openstackx.extras.consoles.Console'''
    _attrs = ['id', 'output', 'type']


class Flavor(APIResourceWrapper):
    '''Simple wrapper around openstackx.admin.flavors.Flavor'''
    _attrs = ['disk', 'id', 'links', 'name', 'ram', 'vcpus']


class Image(APIDictWrapper):
    '''Simple wrapper around glance image dictionary'''
    _attrs = ['checksum', 'container_format', 'created_at', 'deleted',
             'deleted_at', 'disk_format', 'id', 'is_public', 'location',
             'name', 'properties', 'size', 'status', 'updated_at']

    def __getattr__(self, attrname):
        if attrname == "properties":
            return ImageProperties(super(Image, self).__getattr__(attrname))
        else:
            return super(Image, self).__getattr__(attrname)


class ImageProperties(APIDictWrapper):
    '''Simple wrapper around glance image properties dictionary'''
    _attrs = ['architecture', 'image_location', 'image_state', 'kernel_id',
             'project_id', 'ramdisk_id']


class KeyPair(APIResourceWrapper):
    '''Simple wrapper around openstackx.extras.keypairs.Keypair'''
    _attrs = ['fingerprint', 'key_name', 'private_key']


class Server(APIResourceWrapper):
    '''Simple wrapper around openstackx.extras.server.Server

       Preserves the request info so image name can later be retrieved
    '''
    _attrs = ['addresses', 'attrs', 'hostId', 'id', 'imageRef', 'links',
             'metadata', 'name', 'private_ip', 'public_ip', 'status', 'uuid',
             'image_name']

    def __init__(self, apiresource, request):
        super(Server, self).__init__(apiresource)
        self.request = request

    def __getattr__(self, attr):
        if attr == "attrs":
            return ServerAttributes(super(Server, self).__getattr__(attr))
        else:
            return super(Server, self).__getattr__(attr)

    @property
    def image_name(self):
        image = image_get(self.request, self.imageRef)
        return image.name


class ServerAttributes(APIDictWrapper):
    '''Simple wrapper around openstackx.extras.server.Server attributes

       Preserves the request info so image name can later be retrieved
    '''
    _attrs = ['description', 'disk_gb', 'host', 'image_ref', 'kernel_id',
              'key_name', 'launched_at', 'mac_address', 'memory_mb', 'name',
              'os_type', 'project_id', 'ramdisk_id', 'scheduled_at',
              'terminated_at', 'user_data', 'user_id', 'vcpus', 'hostname']


class Services(APIResourceWrapper):
    _attrs = ['disabled', 'host', 'id', 'last_update', 'stats', 'type', 'up',
             'zone']


class SwiftObject(APIResourceWrapper):
    _attrs = ['name']


class Tenant(APIResourceWrapper):
    '''Simple wrapper around openstackx.auth.tokens.Tenant'''
    _attrs = ['id', 'description', 'enabled']


class Token(APIResourceWrapper):
    '''Simple wrapper around openstackx.auth.tokens.Token'''
    _attrs = ['id', 'serviceCatalog', 'tenant_id', 'username']


class Usage(APIResourceWrapper):
    '''Simple wrapper around openstackx.extras.usage.Usage'''
    _attrs = ['begin', 'instances', 'stop', 'tenant_id',
             'total_active_disk_size', 'total_active_instances',
             'total_active_ram_size', 'total_active_vcpus', 'total_cpu_usage',
             'total_disk_usage', 'total_hours', 'total_ram_usage']


class User(APIResourceWrapper):
    '''Simple wrapper around openstackx.extras.users.User'''
    _attrs = ['email', 'enabled', 'id', 'tenantId']


def url_for(request, service_name, admin=False):
    catalog = request.session['serviceCatalog']
    if admin:
        rv = catalog[service_name][0]['adminURL']
    else:
        rv = catalog[service_name][0]['internalURL']
    return rv


def compute_api(request):
    compute = openstack.compute.Compute(
        auth_token=request.session['token'],
        management_url=url_for(request, 'nova'))
    # this below hack is necessary to make the jacobian compute client work
    # TODO(mgius): It looks like this is unused now?
    compute.client.auth_token = request.session['token']
    compute.client.management_url = url_for(request, 'nova')
    LOG.debug('compute_api connection created using token "%s"'
                      ' and url "%s"' %
                      (request.session['token'], url_for(request, 'nova')))
    return compute


def account_api(request):
    LOG.debug('account_api connection created using token "%s"'
                      ' and url "%s"' %
                  (request.session['token'],
                   url_for(request, 'keystone', True)))
    return openstackx.extras.Account(
        auth_token=request.session['token'],
        management_url=url_for(request, 'keystone', True))


def glance_api(request):
    o = urlparse(url_for(request, 'glance'))
    LOG.debug('glance_api connection created for host "%s:%d"' %
                     (o.hostname, o.port))
    return glance.client.Client(o.hostname, o.port)


def admin_api(request):
    LOG.debug('admin_api connection created using token "%s"'
                    ' and url "%s"' %
                    (request.session['token'], url_for(request, 'nova', True)))
    return openstackx.admin.Admin(auth_token=request.session['token'],
                                 management_url=url_for(request, 'nova', True))


def extras_api(request):
    LOG.debug('extras_api connection created using token "%s"'
                     ' and url "%s"' %
                    (request.session['token'], url_for(request, 'nova')))
    return openstackx.extras.Extras(auth_token=request.session['token'],
                                   management_url=url_for(request, 'nova'))


def auth_api():
    LOG.debug('auth_api connection created using url "%s"' %
                   settings.OPENSTACK_KEYSTONE_URL)
    return openstackx.auth.Auth(
            management_url=settings.OPENSTACK_KEYSTONE_URL)


def swift_api():
    return cloudfiles.get_connection(
            settings.SWIFT_ACCOUNT + ":" + settings.SWIFT_USER,
            settings.SWIFT_PASS,
            authurl=settings.SWIFT_AUTHURL)


def console_create(request, instance_id, kind=None):
    return Console(extras_api(request).consoles.create(instance_id, kind))


def flavor_create(request, name, memory, vcpu, disk, flavor_id):
    return Flavor(admin_api(request).flavors.create(
            name, int(memory), int(vcpu), int(disk), flavor_id))


def flavor_delete(request, flavor_id, purge=False):
    admin_api(request).flavors.delete(flavor_id, purge)


def flavor_get(request, flavor_id):
    return Flavor(compute_api(request).flavors.get(flavor_id))


def flavor_list(request):
    return [Flavor(f) for f in extras_api(request).flavors.list()]


def image_create(request, image_meta, image_file):
    return Image(glance_api(request).add_image(image_meta, image_file))


def image_delete(request, image_id):
    return glance_api(request).delete_image(image_id)


def image_get(request, image_id):
    return Image(glance_api(request).get_image(image_id)[0])


def image_list_detailed(request):
    return [Image(i) for i in glance_api(request).get_images_detailed()]


def image_update(request, image_id, image_meta=None):
    image_meta = image_meta and image_meta or {}
    return Image(glance_api(request).update_image(image_id,
                                                  image_meta=image_meta))


def keypair_create(request, name):
    return KeyPair(extras_api(request).keypairs.create(name))


def keypair_delete(request, keypair_id):
    extras_api(request).keypairs.delete(keypair_id)


def keypair_list(request):
    return [KeyPair(key) for key in extras_api(request).keypairs.list()]


def server_create(request, name, image, flavor, user_data, key_name):
    return Server(extras_api(request).servers.create(
            name, image, flavor, user_data=user_data, key_name=key_name),
            request)


def server_delete(request, instance):
    compute_api(request).servers.delete(instance)


def server_get(request, instance_id):
    return Server(compute_api(request).servers.get(instance_id), request)


def server_list(request):
    return [Server(s, request) for s in extras_api(request).servers.list()]


def server_reboot(request,
                  instance_id,
                  hardness=openstack.compute.servers.REBOOT_HARD):
    server = server_get(request, instance_id)
    server.reboot(hardness)


def service_get(request, name):
    return Services(admin_api(request).services.get(name))


def service_list(request):
    return [Services(s) for s in admin_api(request).services.list()]


def service_update(request, name, enabled):
    return Services(admin_api(request).services.update(name, enabled))


def token_get_tenant(request, tenant_id):
    tenants = auth_api().tenants.for_token(request.session['token'])
    for t in tenants:
        if str(t.id) == str(tenant_id):
            return Tenant(t)

    LOG.warning('Unknown tenant id "%s" requested' % tenant_id)


def token_list_tenants(request, token):
    return [Tenant(t) for t in auth_api().tenants.for_token(token)]


def tenant_create(request, tenant_id, description, enabled):
    return Tenant(account_api(request).tenants.create(tenant_id,
                                                      description,
                                                      enabled))


def tenant_get(request, tenant_id):
    return Tenant(account_api(request).tenants.get(tenant_id))


def tenant_list(request):
    return [Tenant(t) for t in account_api(request).tenants.list()]


def tenant_update(request, tenant_id, description, enabled):
    return Tenant(account_api(request).tenants.update(tenant_id,
                                                      description,
                                                      enabled))


def token_create(request, tenant, username, password):
    return Token(auth_api().tokens.create(tenant, username, password))


def token_info(request, token):
    # TODO(mgius): This function doesn't make a whole lot of sense to me.  The
    # information being gathered here really aught to be attached to Token() as
    # part of token_create.  May require modification of openstackx so that the
    # token_create call returns this information as well
    hdrs = {"Content-type": "application/json",
            "X_AUTH_TOKEN": settings.OPENSTACK_ADMIN_TOKEN,
            "Accept": "text/json"}

    o = urlparse(token.serviceCatalog['keystone'][0]['adminURL'])
    conn = httplib.HTTPConnection(o.hostname, o.port)
    conn.request("GET", "/v2.0/tokens/%s" % token.id, headers=hdrs)
    response = conn.getresponse()
    data = json.loads(response.read())

    admin = False
    for role in data['auth']['user']['roleRefs']:
        if role['roleId'] == 'Admin':
            admin = True

    return {'tenant': data['auth']['user']['tenantId'],
            'user': data['auth']['user']['username'],
            'admin': admin}


def usage_get(request, tenant_id, start, end):
    return Usage(extras_api(request).usage.get(tenant_id, start, end))


def usage_list(request, start, end):
    return [Usage(u) for u in extras_api(request).usage.list(start, end)]


def user_create(request, user_id, email, password, tenant_id):
    return User(account_api(request).users.create(
            user_id, email, password, tenant_id))


def user_delete(request, user_id):
    account_api(request).users.delete(user_id)


def user_get(request, user_id):
    return User(account_api(request).users.get(user_id))


def user_list(request):
    return [User(u) for u in account_api(request).users.list()]


def user_update_email(request, user_id, email):
    return User(account_api(request).users.update_email(user_id, email))


def user_update_password(request, user_id, password):
    return User(account_api(request).users.update_password(user_id, password))


def user_update_tenant(request, user_id, tenant_id):
    return User(account_api(request).users.update_tenant(user_id, tenant_id))


def swift_get_containers():
    return [Container(c) for c in swift_api().get_all_containers()]


def swift_create_container(name):
    return Container(swift_api().create_container(name))


def swift_delete_container(name):
    swift_api().delete_container(name)


def swift_get_objects(container_name):
    container = swift_api().get_container(container_name)
    return [SwiftObject(o) for o in container.get_objects()]


def swift_upload_object(container_name, object_name, object_data):
    container = swift_api().get_container(container_name)
    obj = container.create_object(object_name)
    obj.write(object_data)


def swift_delete_object(container_name, object_name):
    container = swift_api().get_container(container_name)
    container.delete_object(object_name)


def swift_get_object_data(container_name, object_name):
    container = swift_api().get_container(container_name)
    return container.get_object(object_name).stream()
