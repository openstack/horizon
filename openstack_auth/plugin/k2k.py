# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from keystoneauth1.identity import v3 as v3_auth

from openstack_auth import exceptions
from openstack_auth.plugin import base
from openstack_auth import utils

LOG = logging.getLogger(__name__)

__all__ = ['K2KAuthPlugin']


class K2KAuthPlugin(base.BasePlugin):

    def get_plugin(self, service_provider=None, auth_url=None, plugins=None,
                   **kwargs):
        """Authenticate using keystone to keystone federation.

        This plugin uses other v3 plugins to authenticate a user to a
        identity provider in order to authenticate the user to a service
        provider

        :param service_provider: service provider ID
        :param auth_url: Keystone auth url
        :param plugins: list of openstack_auth plugins to check
        :returns Keystone2Keystone keystone auth plugin
        """

        # Avoid mutable default arg for plugins
        plugins = plugins or []
        if not service_provider:
            return

        keystone_idp_id = settings.KEYSTONE_PROVIDER_IDP_ID
        if service_provider == keystone_idp_id:
            return None

        for plugin in plugins:
            unscoped_idp_auth = plugin.get_plugin(plugins=plugins,
                                                  auth_url=auth_url, **kwargs)
            if unscoped_idp_auth:
                break
        else:
            LOG.debug('Could not find base authentication backend for '
                      'K2K plugin with the provided credentials.')
            return None

        idp_exception = None
        scoped_idp_auth = None
        unscoped_auth_ref = base.BasePlugin.get_access_info(
            self, unscoped_idp_auth)
        try:
            scoped_idp_auth, __ = self.get_project_scoped_auth(
                unscoped_idp_auth, unscoped_auth_ref,
                recent_project=kwargs['recent_project'])
        except exceptions.KeystoneAuthException as idp_excp:
            idp_exception = idp_excp

        if not scoped_idp_auth or idp_exception:
            msg = _('Identity provider authentication failed.')
            raise exceptions.KeystoneAuthException(msg)

        session = utils.get_session()

        if scoped_idp_auth.get_sp_auth_url(session, service_provider) is None:
            msg = _('Could not find service provider ID on keystone.')
            raise exceptions.KeystoneAuthException(msg)

        unscoped_auth = v3_auth.Keystone2Keystone(
            base_plugin=scoped_idp_auth,
            service_provider=service_provider)
        return unscoped_auth

    def get_access_info(self, unscoped_auth):
        """Get the access info object

        We attempt to get the auth ref. If it fails and if the K2K auth plugin
        was being used then we will prepend a message saying that the error was
        on the service provider side.
        :param unscoped_auth: Keystone auth plugin for unscoped user
        :returns: keystoneclient.access.AccessInfo object
        """
        try:
            unscoped_auth_ref = base.BasePlugin.get_access_info(
                self, unscoped_auth)
        except exceptions.KeystoneAuthException as excp:
            msg = _('Service provider authentication failed. %s')
            raise exceptions.KeystoneAuthException(msg % str(excp))
        return unscoped_auth_ref
