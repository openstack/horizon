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
        
from django.conf import settings

from keystoneclient.v3 import client
        
class KeystoneManager(object):
    """Encapsulates all the logic for communicating with the keystone server.

    The IdM has its own admin account in the keystone server, and uses it to perform
    operations like create users, projects, etc. when there is no user with admin rights
    (for example, when user registration) to overcome the Keystone limitations.
    """

    def __init__(self, **kwargs ):
        super(KeystoneManager, self).__init__()

        self.AUTH_URL = getattr(settings,'OPENSTACK_KEYSTONE_URL')
        credentials = getattr(settings, 'OPENSTACK_KEYSTONE_ADMIN_CREDENTIALS')
        self.__dict__.update(credentials)
        
    def _login(self):
        """ Get an authorized token to perform operations on the keystone backend """
        keystone = client.Client(username=self.USERNAME, 
                                    password=self.PASSWORD, 
                                    project_name=self.TENANT, 
                                    auth_url=self.AUTH_URL)
        return keystone

    def _create_user(self,keystone,name,domain,password,email,default_project,enabled=False):
        user = keystone.users.create(name,domain=domain,password=password,email=email,
                                        default_project=default_project, enabled=enabled)
        return user

    def _update_user(self,keystone,user,enabled=False,password=None):
        user = keystone.users.update(user,enabled=enabled,password=password)
        return user

    def _get_user(self,keystone,user_id):
        user = keystone.users.get(user_id)
        return user

    def _find_user(self,keystone,email=None,name=None):
        user = keystone.users.find(email=email,name=name)
        return user

    def _create_project(self,keystone,name,domain,description=None,enabled=False):
        project = keystone.projects.create(name,domain=domain,
                                description=description, enabled=enabled)
        return project

    def _update_project(self,keystone,project,enabled=False):
        project = keystone.projects.update(project,enabled=enabled)
        return project

    def _grant_admin_role(self,keystone, user, project):
        role = keystone.roles.find(name='admin')
        keystone.roles.grant(role,user=user,project=project)
        return role

    def _create_domain(self):
        pass

    def _get_default_domain(self,keystone):
        domain = keystone.domains.get(self.DOMAIN)
        return domain

    def register_user(self,name,email,password):
        keystone = self._login()
        default_domain = self._get_default_domain(keystone)
        default_project = self._create_project(keystone,name,default_domain)
        new_user = self._create_user(keystone,name,default_domain,password,email,default_project)
        role = self._grant_admin_role(keystone,new_user,default_project)
        return new_user
        
    def activate_user(self,user_id):
        keystone = self._login()
        #default_domain = self._get_default_domain(keystone)
        user = self._get_user(keystone,user_id)
        project = self._update_project(keystone,user.default_project_id,enabled=True)
        user = self._update_user(keystone,user,enabled=True)
        return user

    def change_password(self,user_email,new_password):
        keystone = self._login()
        user = self._find_user(keystone,email=user_email)
        user = self._update_user(keystone,user,password=new_password)
        return user

    def check_user(self,name):
        keystone = self._login()
        user = self._find_user(keystone,name=name)
        return user

    def check_email(self,email):
        keystone = self._login()
        user = self._find_user(keystone,email=email)
        return user