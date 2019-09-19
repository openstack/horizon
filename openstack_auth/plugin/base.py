# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import abc
import logging
import re

from django.utils.translation import ugettext_lazy as _
from keystoneauth1 import exceptions as keystone_exceptions
from keystoneclient.v3 import client as v3_client
import six

from openstack_auth import exceptions
from openstack_auth import utils

LOG = logging.getLogger(__name__)
__all__ = ['BasePlugin']


@six.add_metaclass(abc.ABCMeta)
class BasePlugin(object):
    """Base plugin to provide ways to log in to dashboard.

    Provides a framework for keystoneclient plugins that can be used with the
    information provided to return an unscoped token.
    """

    @abc.abstractmethod
    def get_plugin(self, auth_url=None, **kwargs):
        """Create a new plugin to attempt to authenticate.

        Given the information provided by the login providers attempt to create
        an authentication plugin that can be used to authenticate the user.

        If the provided login information does not contain enough information
        for this plugin to proceed then it should return None.

        :param str auth_url: The URL to authenticate against.

        :returns: A plugin that will be used to authenticate or None if the
                  plugin cannot authenticate with the data provided.
        :rtype: keystoneclient.auth.BaseAuthPlugin
        """
        return None

    @property
    def keystone_version(self):
        """The Identity API version as specified in the settings file."""
        return utils.get_keystone_version()

    def list_projects(self, session, auth_plugin, auth_ref=None):
        """List the projects that are accessible to this plugin.

        Query the keystone server for all projects that this authentication
        token can be rescoped to.

        This function is overrideable by plugins if they use a non-standard
        mechanism to determine projects.

        :param session: A session object for communication:
        :type session: keystoneclient.session.Session
        :param auth_plugin: The auth plugin returned by :py:meth:`get_plugin`.
        :type auth_plugin: keystoneclient.auth.BaseAuthPlugin
        :param auth_ref: The current authentication data. This is optional as
                         future auth plugins may not have auth_ref data and all
                         the required information should be available via the
                         auth_plugin.
        :type auth_ref: keystoneclient.access.AccessInfo` or None.

        :raises: exceptions.KeystoneAuthException on lookup failure.

        :returns: A list of projects. This currently accepts returning both v2
                  or v3 keystoneclient projects objects.
        """
        try:
            client = v3_client.Client(session=session, auth=auth_plugin)
            if auth_ref.is_federated:
                return client.federation.projects.list()
            else:
                return client.projects.list(user=auth_ref.user_id)

        except (keystone_exceptions.ClientException,
                keystone_exceptions.AuthorizationFailure):
            msg = _('Unable to retrieve authorized projects.')
            raise exceptions.KeystoneRetrieveProjectsException(msg)

    def list_domains(self, session, auth_plugin, auth_ref=None):
        try:
            client = v3_client.Client(session=session, auth=auth_plugin)
            return client.auth.domains()
        except (keystone_exceptions.ClientException,
                keystone_exceptions.AuthorizationFailure):
            msg = _('Unable to retrieve authorized domains.')
            raise exceptions.KeystoneRetrieveDomainsException(msg)

    def get_access_info(self, keystone_auth):
        """Get the access info from an unscoped auth

        This function provides the base functionality that the
        plugins will use to authenticate and get the access info object.

        :param keystone_auth: keystoneauth1 identity plugin
        :raises: exceptions.KeystoneAuthException on auth failure
        :returns: keystoneclient.access.AccessInfo
        """
        session = utils.get_session()

        try:
            unscoped_auth_ref = keystone_auth.get_access(session)
        except keystone_exceptions.ConnectFailure as exc:
            LOG.error(str(exc))
            msg = _('Unable to establish connection to keystone endpoint.')
            raise exceptions.KeystoneConnectionException(msg)
        except (keystone_exceptions.Unauthorized,
                keystone_exceptions.Forbidden,
                keystone_exceptions.NotFound) as exc:
            msg = str(exc)
            LOG.debug(msg)
            match = re.match(r"The password is expired and needs to be changed"
                             r" for user: ([^.]*)[.].*", msg)
            if match:
                exc = exceptions.KeystonePassExpiredException(
                    _('Password expired.'))
                exc.user_id = match.group(1)
                raise exc
            msg = _('Invalid credentials.')
            raise exceptions.KeystoneCredentialsException(msg)
        except (keystone_exceptions.ClientException,
                keystone_exceptions.AuthorizationFailure) as exc:
            msg = _("An error occurred authenticating. "
                    "Please try again later.")
            LOG.debug(str(exc))
            raise exceptions.KeystoneAuthException(msg)
        return unscoped_auth_ref

    def get_project_scoped_auth(self, unscoped_auth, unscoped_auth_ref,
                                recent_project=None):
        """Get the project scoped keystone auth and access info

        This function returns a project scoped keystone token plugin
        and AccessInfo object.

        :param unscoped_auth: keystone auth plugin
        :param unscoped_auth_ref: keystoneclient.access.AccessInfo` or None.
        :param recent_project: project that we should try to scope to
        :return: keystone token auth plugin, AccessInfo object
        """
        auth_url = unscoped_auth.auth_url
        session = utils.get_session()

        projects = self.list_projects(
            session, unscoped_auth, unscoped_auth_ref)
        # Attempt to scope only to enabled projects
        projects = [project for project in projects if project.enabled]

        # if a most recent project was found, try using it first
        if recent_project:
            for pos, project in enumerate(projects):
                if project.id == recent_project:
                    # move recent project to the beginning
                    projects.pop(pos)
                    projects.insert(0, project)
                    break

        scoped_auth = None
        scoped_auth_ref = None
        for project in projects:
            token = unscoped_auth_ref.auth_token
            scoped_auth = utils.get_token_auth_plugin(auth_url,
                                                      token=token,
                                                      project_id=project.id)
            try:
                scoped_auth_ref = scoped_auth.get_access(session)
            except (keystone_exceptions.ClientException,
                    keystone_exceptions.AuthorizationFailure):
                LOG.info('Attempted scope to project %s failed, will attempt '
                         'to scope to another project.', project.name)
            else:
                break

        return scoped_auth, scoped_auth_ref

    def get_domain_scoped_auth(self, unscoped_auth, unscoped_auth_ref,
                               domain_name=None):
        """Get the domain scoped keystone auth and access info

        This function returns a domain scoped keystone token plugin
        and AccessInfo object.

        :param unscoped_auth: keystone auth plugin
        :param unscoped_auth_ref: keystoneclient.access.AccessInfo` or None.
        :param domain_name: domain that we should try to scope to
        :return: keystone token auth plugin, AccessInfo object
        """
        session = utils.get_session()
        auth_url = unscoped_auth.auth_url

        if domain_name:
            domains = [domain_name]
        else:
            domains = self.list_domains(session,
                                        unscoped_auth,
                                        unscoped_auth_ref)
            domains = [domain.name for domain in domains if domain.enabled]

        # domain support can require domain scoped tokens to perform
        # identity operations depending on the policy files being used
        # for keystone.
        domain_auth = None
        domain_auth_ref = None
        for _name in domains:
            token = unscoped_auth_ref.auth_token
            domain_auth = utils.get_token_auth_plugin(
                auth_url,
                token,
                domain_name=_name)
            try:
                domain_auth_ref = domain_auth.get_access(session)
            except (keystone_exceptions.ClientException,
                    keystone_exceptions.AuthorizationFailure):
                LOG.info('Attempted scope to domain %s failed, will attempt '
                         'to scope to another domain.', _name)
            else:
                if len(domains) > 1:
                    LOG.info("More than one valid domain found for user %s,"
                             " scoping to %s",
                             unscoped_auth_ref.user_id, _name)
                break
        return domain_auth, domain_auth_ref
