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
    operations like create users, tenants, etc. when there is no user with admin rights
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
                                    tenant_name=self.TENANT, 
                                    auth_url=self.AUTH_URL)
        return keystone

    def _create_user(self,name,domain,password,email,default_project,enabled=False):
        keystone = self._login()
        user = keystone.users.create(name,domain=domain,password=password,email=email,
                                        default_project=default_project, enabled=enabled)
        return user

    def _create_tenant(self,name,domain,description=None,enabled=False):
        keystone = self._login()
        tenant = keystone.projects.create(name,domain=domain,
                                description=description, enabled=enabled)
        return tenant

    def _create_domain(self):
        pass

    def _get_default_domain(self):
        keystone = self._login()
        domain = keystone.domains.get(self.DOMAIN)
        return domain

    def register_user(self,name,email,password):
        default_domain = self._get_default_domain()
        default_project = self._create_tenant(name,default_domain)
        new_user = self._create_user(name,default_domain,password,email,default_project)
        return new_user
        


        