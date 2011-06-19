# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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
Simple API for interacting with Nova projects.
"""

import boto
import boto.ec2.volume
import boto.exception
import boto.s3
from django.conf import settings
from django_openstack.core import connection
from django_openstack.nova.exceptions import wrap_nova_error


class ProjectManager(object):
    def __init__(self, username, project, region):
        self.username = username
        self.projectname = project.projectname
        self.projectManagerId = project.projectManagerId
        self.region = region

    def get_openstack_connection(self):
        """
        Returns a boto connection for a user's project.
        """
        openstack = connection.get_nova_admin_connection()
        return openstack.connection_for(self.username,
                                   self.projectname,
                                   clc_url=self.region['endpoint'],
                                   region=self.region['name'])

    def get_zip(self):
        """
        Returns a buffer of a zip file containing signed credentials
        for the project's Nova user.
        """
        openstack = connection.get_nova_admin_connection()
        return openstack.get_zip(self.username, self.projectname)

    def get_images(self, image_ids=None):
        conn = self.get_openstack_connection()
        images = conn.get_all_images(image_ids=image_ids)
        sorted_images = [i for i in images if i.ownerId == self.username] + \
                        [i for i in images if i.ownerId != self.username]

        return [i for i in sorted_images if i.type == 'machine'
                and i.location.split('/')[0] != 'openstack']

    def get_image(self, image_id):
        try:
            return self.get_images(image_ids=[image_id])[0]
        except IndexError:
            return None

    @wrap_nova_error
    def deregister_image(self, image_id):
        """
        Removes the image's listing but leaves the image
        and manifest in the object store in tact.
        """
        conn = self.get_openstack_connection()
        return conn.deregister_image(image_id)

    @wrap_nova_error
    def update_image(self, image_id, display_name=None, description=None):
        conn = self.get_openstack_connection()
        params = {
                    'ImageId': image_id,
                    'DisplayName': display_name,
                    'Description': description
                 }
        return conn.get_object('UpdateImage', params, boto.ec2.image.Image)

    @wrap_nova_error
    def modify_image_attribute(self, image_id, attribute=None, operation=None,
                               groups='all'):
        conn = self.get_openstack_connection()
        return conn.modify_image_attribute(image_id,
                                           attribute=attribute,
                                           operation=operation,
                                           groups=groups,)

    @wrap_nova_error
    def run_instances(self, image_id, instance_type, count,
                      addressing_type='private', key_name=None,
                      display_name=None, user_data=None):
        """
        Runs instances of the specified image id.
        """
        conn = self.get_openstack_connection()
        params = {
            'ImageId': image_id,
            'InstanceType': instance_type,
            'MinCount': count,
            'MaxCount': count,
            'addressing_type': addressing_type,
        }
        if key_name is not None:
            params['key_name'] = key_name
        if display_name is not None:
            params['display_name'] = display_name
        if user_data is not None:
            params['UserData'] = user_data
        return conn.get_object('RunInstances', params,
                boto.ec2.instance.Reservation, verb='POST')

    def get_instance_count(self):
        """
        Returns the number of active instances in this project
        or None if unknown.
        """
        try:
            return len(self.get_instances())
        except:
            return None

    @wrap_nova_error
    def get_instances(self):
        """
        Returns all instances in this project.
        """
        conn = self.get_openstack_connection()
        reservations = conn.get_all_instances()
        instances = []
        for reservation in reservations:
            for instance in reservation.instances:
                instances.append(instance)
        return instances

    @wrap_nova_error
    def get_instance(self, instance_id):
        """
        Returns detail about the specified instance.
        """
        conn = self.get_openstack_connection()
        # TODO: Refactor this once openstack's describe_instances
        # filters by instance_id.
        reservations = conn.get_all_instances()
        for reservation in reservations:
            for instance in reservation.instances:
                if instance.id == instance_id:
                    return instance
        return None

    @wrap_nova_error
    def update_instance(self, instance_id, updates):
        conn = self.get_openstack_connection()
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
        except boto.exception.S3ResponseError, e:
            if e.code == "NoSuchBucket":
                return None
            else:
                raise e

        key = bucket.get_key(graph_name)

        return key.read()

    @wrap_nova_error
    def terminate_instance(self, instance_id):
        """ Terminates the specified instance within this project. """
        conn = self.get_openstack_connection()
        conn.terminate_instances([instance_id])

    @wrap_nova_error
    def get_security_groups(self):
        """
        Returns all security groups associated with this project.
        """
        conn = self.get_openstack_connection()
        groups = []

        for g in conn.get_all_security_groups():
            # Do not show vpn group.
            #if g.name != 'vpn-secgroup':
            groups.append(g)

        return groups

    @wrap_nova_error
    def get_security_group(self, name):
        """
        Returns the specified security group for this project.
        """
        conn = self.get_openstack_connection()

        try:
            return conn.get_all_security_groups(
                    groupnames=name.encode('ASCII'))[0]
        except IndexError:
            return None

    @wrap_nova_error
    def has_security_group(self, name):
        """
        Indicates whether a security group with the specified name
        exists in this project.
        """
        return self.get_security_group(name) is not None

    @wrap_nova_error
    def create_security_group(self, name, description):
        """
        Creates a new security group in this project.
        """
        conn = self.get_openstack_connection()
        return conn.create_security_group(name, description)

    @wrap_nova_error
    def delete_security_group(self, name):
        """
        Deletes a security group from the project.
        """
        conn = self.get_openstack_connection()
        return conn.delete_security_group(name=name)

    @wrap_nova_error
    def authorize_security_group(self, group_name, ip_protocol, from_port,
                                 to_port):
        """
        Authorizes a rule for the specified security group.
        """
        conn = self.get_openstack_connection()
        return conn.authorize_security_group(
            group_name=group_name,
            ip_protocol=ip_protocol,
            from_port=from_port,
            to_port=to_port,
            cidr_ip='0.0.0.0/0')

    @wrap_nova_error
    def revoke_security_group(self, group_name, ip_protocol, from_port,
                              to_port):
        """
        Revokes a rule for the specified security group.
        """
        conn = self.get_openstack_connection()
        return conn.revoke_security_group(
            group_name=group_name,
            ip_protocol=ip_protocol,
            from_port=from_port,
            to_port=to_port,
            cidr_ip='0.0.0.0/0')

    @wrap_nova_error
    def get_key_pairs(self):
        """
        Returns all key pairs associated with this project.
        """
        conn = self.get_openstack_connection()
        keys = []

        for k in conn.get_all_key_pairs():
            # Do not show vpn key.
            if k.name != 'vpn-key':
                keys.append(k)

        return keys

    @wrap_nova_error
    def get_key_pair(self, name):
        """
        Returns the specified security group for this project.
        """
        conn = self.get_openstack_connection()

        try:
            return conn.get_all_key_pairs(keynames=name.encode('ASCII'))[0]
        except IndexError:
            return None

    @wrap_nova_error
    def has_key_pair(self, name):
        """
        Indicates whether a key pair with the specified name exists
        in this project.
        """
        return self.get_key_pair(name) != None

    @wrap_nova_error
    def create_key_pair(self, name):
        """
        Creates a new key pair for this project.
        """
        conn = self.get_openstack_connection()
        return conn.create_key_pair(name)

    @wrap_nova_error
    def delete_key_pair(self, name):
        """
        Deletes a new key pair from this project.
        """
        conn = self.get_openstack_connection()
        conn.delete_key_pair(name)

    @wrap_nova_error
    def get_volumes(self):
        """
        Returns all volumes in this project.
        """
        conn = self.get_openstack_connection()
        return conn.get_all_volumes()

    @wrap_nova_error
    def create_volume(self, size, display_name=None, display_description=None,
                      snapshot=None):
        conn = self.get_openstack_connection()
        params = {'Size': size, 'DisplayName': display_name,
                  'DisplayDescription': display_description}
        return conn.get_object('CreateVolume', params, boto.ec2.volume.Volume)

    @wrap_nova_error
    def delete_volume(self, volume_id):
        conn = self.get_openstack_connection()
        return conn.delete_volume(volume_id)

    @wrap_nova_error
    def attach_volume(self, volume_id, instance_id, device):
        conn = self.get_openstack_connection()
        return conn.attach_volume(volume_id, instance_id, device)

    @wrap_nova_error
    def detach_volume(self, volume_id):
        conn = self.get_openstack_connection()
        return conn.detach_volume(volume_id)
