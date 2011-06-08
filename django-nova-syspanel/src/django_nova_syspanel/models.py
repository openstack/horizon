import sys
import boto
import boto.exception
import boto.s3
from boto.ec2.volume import Volume
from xml.dom import minidom

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models.signals import post_save
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _

from nova_adminclient import NovaAdminClient

project_permissions = ('admin',)


class NovaResponseError(Exception):
    def __init__(self, ec2error):
        if ec2error.reason == 'Forbidden':
            self.code = _('Forbidden')
            self.message = _('Forbidden')
            return

        dom = minidom.parseString(ec2error.body)
        err = dom.getElementsByTagName('Errors')[0]

        try:
            self.code = err.getElementsByTagName('Code')[0].childNodes[0].data
        except IndexError:
            self.code = 'Unknown'

        try:
            self.message = err.getElementsByTagName('Message')[0].childNodes[0].data
        except IndexError:
            self.message = _('An unexpected error occurred.  Please try your request again.')

        dom.unlink()

    def __str__(self):
        return '%s (%s)' % (self.message, self.code)


def handle_nova_error(fn):
    def decorator(view_func):
        def wrapper(*args, **kwargs):
            try:
                return view_func(*args, **kwargs)
            except boto.exception.EC2ResponseError, e:
                if e.reason == 'Forbidden':
                    raise PermissionDenied()
                else:
                    raise NovaResponseError(e)
        return wrapper
    return decorator(fn)


def get_nova_admin_connection():
    """
    Returns a Nova administration connection.
    """
    return NovaAdminClient(
        clc_url=settings.NOVA_DEFAULT_ENDPOINT,
        region=settings.NOVA_DEFAULT_REGION,
        access_key=settings.NOVA_ACCESS_KEY,
        secret_key=settings.NOVA_SECRET_KEY)


class VolumeInfo(object):
    """Foo"""

    def __init__(self, connection=None, username=None, endpoint=None):
        self.connection = connection
        self.username = username
        self.endpoint = endpoint

        self.id = None
        self.create_time = None
        self.status = None
        self.size = None
        self.snapshot_id = None
        self.attach_data = None
        self.zone = None

        self.display_name = None
        self.display_description = None

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'volumeId':
            self.id = str(value)
        elif name == 'size':
            self.size = int(value)
        elif name == 'status':
            self.status = str(value)
        elif name == 'displayName':
            self.display_name = str(value)
        elif name == 'displayDescription':
            self.display_description = str(value)
        else:
            setattr(self, name, str(value))


class ProjectManager(object):
    def __init__(self, username, project, region):
        self.username = username
        self.projectname = project.projectname
        self.projectManagerId = project.projectManagerId
        self.region = region

    def get_nova_connection(self):
        """
        Returns a boto connection for a user's project.
        """
        nova = get_nova_admin_connection()
        return nova.connection_for(self.username,
                                   self.projectname,
                                   clc_url=self.region['endpoint'],
                                   region=self.region['name'])

    def get_zip(self):
        """
        Returns a buffer of a zip file containing signed credentials
        for the project's Nova user.
        """
        nova = get_nova_admin_connection()
        return nova.get_zip(self.username, self.projectname)

    def get_images(self, image_ids=None):
        conn = self.get_nova_connection()
        images = conn.get_all_images(image_ids=image_ids)
        sorted_images = [i for i in images if i.ownerId == self.username] + \
                        [i for i in images if i.ownerId != self.username]

        return [i for i in sorted_images
                if i.type == 'machine' and i.location.split('/')[0] != 'nova']

    def get_image(self, image_id):
        try:
            return self.get_images(image_ids=[image_id, ])[0]
        except IndexError:
            return None

    @handle_nova_error
    def deregister_image(self, image_id):
        """
        Removes the image's listing but leaves the image
        and manifest in the object store in tact.
        """
        conn = self.get_nova_connection()
        return conn.deregister_image(image_id)

    @handle_nova_error
    def update_image(self, image_id, display_name=None, description=None):
        conn = self.get_nova_connection()
        params = {'ImageId': image_id,
                  'DisplayName': display_name,
                  'Description': description}
        return conn.get_object('UpdateImage', params, boto.ec2.image.Image)

    @handle_nova_error
    def run_instances(self, image_id, **kwargs):
        """
        Runs instances of the specified image id.
        """
        conn = self.get_nova_connection()
        return conn.run_instances(image_id, **kwargs)

    def get_instance_count(self):
        """
        Returns the number of active instances in this project
        or None if unknown.
        """
        try:
            return len(self.get_instances())
        except:
            return None

    @handle_nova_error
    def get_instances(self):
        """
        Returns all instances in this project.
        """
        conn = self.get_nova_connection()
        reservations = conn.get_all_instances()
        instances = []
        for reservation in reservations:
            for instance in reservation.instances:
                instances.append(instance)
        return instances

    @handle_nova_error
    def get_instance(self, instance_id):
        """
        Returns detail about the specified instance.
        """
        conn = self.get_nova_connection()
        # TODO: Refactor this once nova's describe_instances filters by instance_id.
        reservations = conn.get_all_instances()
        for reservation in reservations:
            for instance in reservation.instances:
                if instance.id == instance_id:
                    return instance
        return None

    @handle_nova_error
    def update_instance(self, instance_id, updates):
        conn = self.get_nova_connection()
        params = {'InstanceId': instance_id,
                  'DisplayName': updates['nickname'],
                  'DisplayDescription': updates['description']}
        return conn.get_object('UpdateInstance', params,
                               boto.ec2.instance.Instance)

    def get_instance_graph(self, region, instance_id, graph_name):
        # TODO(devcamcar): Need better support for multiple regions.
        #                  Need a way to get object store by region.
        s3 = boto.s3.connection.S3Connection(
            aws_access_key_id=settings.NOVA_ACCESS_KEY,
            aws_secret_access_key=settings.NOVA_SECRET_KEY,
            is_secure=False,
            calling_format=boto.s3.connection.OrdinaryCallingFormat(),
            port=3333,
            host=settings.NOVA_CLC_IP)
        key = '_%s.monitor' % instance_id

        try:
            bucket = s3.get_bucket(key, validate=False)
        except S3ResponseError, e:
            if e.code == "NoSuchBucket":
                return None
            else:
                raise e

        key = bucket.get_key(graph_name)

        return key.read()

    @handle_nova_error
    def terminate_instance(self, instance_id):
        """ Terminates the specified instance within this project. """
        conn = self.get_nova_connection()
        conn.terminate_instances([instance_id])

    @handle_nova_error
    def get_security_groups(self):
        """
        Returns all security groups associated with this project.
        """
        conn = self.get_nova_connection()
        groups = []

        for g in conn.get_all_security_groups():
            # Do not show vpn group.
            #if g.name != 'vpn-secgroup':
            groups.append(g)

        return groups

    @handle_nova_error
    def get_security_group(self, name):
        """
        Returns the specified security group for this project.
        """
        conn = self.get_nova_connection()

        try:
            return conn.get_all_security_groups(groupnames=name.encode('ASCII'))[0]
        except IndexError:
            return None

    @handle_nova_error
    def has_security_group(self, name):
        """
        Indicates whether a security group with the specified name
        exists in this project.
        """
        return self.get_security_group(name) != None

    @handle_nova_error
    def create_security_group(self, name, description):
        """
        Creates a new security group in this project.
        """
        conn = self.get_nova_connection()
        return conn.create_security_group(name, description)

    @handle_nova_error
    def delete_security_group(self, name):
        """
        Deletes a security group from the project.
        """
        conn = self.get_nova_connection()
        return conn.delete_security_group(name=name)

    @handle_nova_error
    def authorize_security_group(self, group_name, ip_protocol, from_port, to_port):
        """
        Authorizes a rule for the specified security group.
        """
        conn = self.get_nova_connection()
        return conn.authorize_security_group(
            group_name=group_name,
            ip_protocol=ip_protocol,
            from_port=from_port,
            to_port=to_port,
            cidr_ip='0.0.0.0/0')

    @handle_nova_error
    def revoke_security_group(self, group_name, ip_protocol, from_port, to_port):
        """
        Revokes a rule for the specified security group.
        """
        conn = self.get_nova_connection()
        return conn.revoke_security_group(
            group_name=group_name,
            ip_protocol=ip_protocol,
            from_port=from_port,
            to_port=to_port,
            cidr_ip='0.0.0.0/0')

    @handle_nova_error
    def get_key_pairs(self):
        """
        Returns all key pairs associated with this project.
        """
        conn = self.get_nova_connection()
        keys = []

        for k in conn.get_all_key_pairs():
            # Do not show vpn key.
            if k.name != 'vpn-key':
                keys.append(k)

        return keys

    @handle_nova_error
    def get_key_pair(self, name):
        """
        Returns the specified security group for this project.
        """
        conn = self.get_nova_connection()

        try:
            return conn.get_all_key_pairs(keynames=name.encode('ASCII'))[0]
        except IndexError:
            return None

    @handle_nova_error
    def has_key_pair(self, name):
        """
        Indicates whether a key pair with the specified name
        exists in this project.
        """
        return self.get_key_pair(name) != None

    @handle_nova_error
    def create_key_pair(self, name):
        """
        Creates a new key pair for this project.
        """
        conn = self.get_nova_connection()
        return conn.create_key_pair(name)

    @handle_nova_error
    def delete_key_pair(self, name):
        """
        Deletes a new key pair from this project.
        """
        conn = self.get_nova_connection()
        conn.delete_key_pair(name)

    @handle_nova_error
    def get_volumes(self):
        """
        Returns all volumes in this project.
        """
        conn = self.get_nova_connection()
        return conn.get_all_volumes()

    @handle_nova_error
    def create_volume(self, size, display_name=None, display_description=None,
                      snapshot=None):
        conn = self.get_nova_connection()
        params = {'Size': size, 'DisplayName': display_name,
                  'DisplayDescription': display_description}
        return conn.get_object('CreateVolume', params, boto.ec2.volume.Volume)

    @handle_nova_error
    def delete_volume(self, volume_id):
        conn = self.get_nova_connection()
        return conn.delete_volume(volume_id)

    @handle_nova_error
    def attach_volume(self, volume_id, instance_id, device):
        conn = self.get_nova_connection()
        return conn.attach_volume(volume_id, instance_id, device)

    @handle_nova_error
    def detach_volume(self, volume_id):
        conn = self.get_nova_connection()
        return conn.detach_volume(volume_id)


def user_post_save(sender, instance, created, *args, **kwargs):
    """
    Creates a Nova User when a new Django User is created.
    """
    if created:
        nova = get_nova_admin_connection()
        if not nova.has_user(instance.username):
            nova.create_user(instance.username)
post_save.connect(user_post_save, User, dispatch_uid='django.contrib.auth.models.User.post_save')
