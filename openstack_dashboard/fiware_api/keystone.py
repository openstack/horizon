# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from django.conf import settings
from keystoneclient import exceptions as ks_exceptions
from keystoneclient.v3 import client

# TODO(garcianavalon)caching and efficiency with the client object.
def fiwareclient(self):
    """Encapsulates all the logic for communicating with the modified keystone server.

    The IdM has its own admin account in the keystone server, and uses it to perform
    operations like create users, projects, etc. when there is no user with admin rights
    (for example, when user registration) to overcome the Keystone limitations.

    Also adds the methods to operate with the OAuth2.0 extension.
    """
    conf_params = getattr(settings, 'OPENSTACK_KEYSTONE_ADMIN_CREDENTIALS')
    conf_params['AUTH_URL'] = getattr(settings,'OPENSTACK_KEYSTONE_URL')
    # TODO(garcianavalon) replace with our client
    keystone = client.Client(username=conf_params['USERNAME'],
                            password=conf_params['PASSWORD'],
                            project=conf_params['PROJECT'],
                            auth_url=conf_params['AUTH_URL'])
    return keystone
        



def _find_user(keystone,email=None,name=None):
    # FIXME(garcianavalon) I dont know why but find by email returns a NoUniqueMatch 
    # exception so we do it by hand filtering the python dictionary, 
    # which is extremely inneficient...
    if name:
        user = keystone.users.find(name=name)
        return user
    elif email:
        user_list = keystone.users.list()
        for user in user_list:
            if user.email == email:
                return user
        # consistent behaviour with the keystoneclient api
        msg = "No user matching email=%s." % email
        raise ks_exceptions.NotFound(404, msg)

def _grant_admin_role(keystone, user, project):
    # TODO(garciavalon) this admin role name depends on the keystone instalation,
    # document this or load it as a config option
    role = keystone.roles.find(name='admin')
    keystone.roles.grant(role,user=user,project=project)
    return role

def register_user(name,email,password):
    keystone = fiwareclient()
    domain = getattr(settings, 'OPENSTACK_KEYSTONE_ADMIN_CREDENTIALS')['DOMAIN']
    default_domain = keystone.domains.get(domain)
    default_project = keystone.projects.create(name,domain=default_domain)
    new_user = keystone.users.create(name,
                                    domain=default_domain,
                                    password=password,
                                    email=email,
                                    default_project=default_project)
    role = _grant_admin_role(keystone,new_user,default_project)
    return new_user
    
def activate_user(user_id):
    keystone = fiwareclient()
    user = keystone.users.get(user_id)
    project = keystone.projects.update(user.default_project_id,enabled=True)
    user = keystone.users.update(user,enabled=True)
    return user

def change_password(user_email,new_password):
    keystone = fiwareclient()
    user = _find_user(keystone,email=user_email)
    user = keystone.users.update(user,password=new_password,enabled=True)
    return user

def check_user(name):
    keystone = fiwareclient()
    user = _find_user(keystone,name=name)
    return user

def check_email(email):
    keystone = fiwareclient()
    user = _find_user(keystone,email=email)
    return user