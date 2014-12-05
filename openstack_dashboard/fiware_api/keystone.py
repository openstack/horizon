# Copyright (C) 2014 Universidad Politecnica de Madrid
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
import requests

from django.conf import settings
from openstack_dashboard import api

# check that we have the correct version of the keystoneclient
try:
    from keystoneclient.v3.contrib.oauth2 import core
except ImportError, e:
    raise ImportError(e,
                'You dont have setup correctly the extended keystoneclient. \
                ask garcianavalon (Kike) or look at the wiki at github')
else:
    from keystoneclient import exceptions as ks_exceptions
    from keystoneclient import session
    from keystoneclient.auth.identity import v3
    from keystoneclient.v3 import client
    from keystoneclient.v3.contrib.oauth2 import auth

LOG = logging.getLogger('idm_logger')

def fiwareclient(session=None, request=None):# TODO(garcianavalon) use this
    """Encapsulates all the logic for communicating with the modified keystone server.

    The IdM has its own admin account in the keystone server, and uses it to perform
    operations like create users, projects, etc. when there is no user with admin rights
    (for example, when user registration) to overcome the Keystone limitations.

    Also adds the methods to operate with the OAuth2.0 extension.
    """
    # TODO(garcianavalon) find a way to integrate this with the existng keystone api
    # TODO(garcianavalon)caching and efficiency with the client object.
    if not session:
        session = _password_session()
    keystone = client.Client(session=session)
    return keystone
        
def _oauth2_session(access_token_id):
    auth = auth.OAuth2(access_token=access_token_id)
    return session.Session(auth=auth)

def _password_session():
    conf_params = getattr(settings, 'OPENSTACK_KEYSTONE_ADMIN_CREDENTIALS')
    conf_params['AUTH_URL'] = getattr(settings, 'OPENSTACK_KEYSTONE_URL')
    LOG.debug('Creating a new keystoneclient password session to \
        {0} for user: {1}'.format(conf_params['AUTH_URL'], conf_params['USERNAME']))
    auth = v3.Password(auth_url=conf_params['AUTH_URL'],
                    username=conf_params['USERNAME'],
                    password=conf_params['PASSWORD'],
                    project_name=conf_params['PROJECT'],
                    user_domain_id=conf_params['DOMAIN'],
                    project_domain_id=conf_params['DOMAIN'])
    return session.Session(auth=auth)

# USER REGISTRATION
def _find_user(keystone, email=None, name=None):
    # NOTE(garcianavalon) I dont know why but find by email returns a NoUniqueMatch 
    # exception so we do it by hand filtering the python dictionary, 
    # which is extremely inneficient
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

def _grant_role(keystone, role, user, project):
    role = keystone.roles.find(name=role)
    keystone.roles.grant(role, user=user, project=project)
    return role

def register_user(name, email, password):
    keystone = fiwareclient()
    domain = getattr(settings, 'OPENSTACK_KEYSTONE_ADMIN_CREDENTIALS')['DOMAIN']
    default_domain = keystone.domains.get(domain)
    # set a new attribute is_default to filter it later
    default_project = keystone.projects.create(name, domain=default_domain, is_default=True)
    new_user = keystone.users.create(name,
                                    domain=default_domain,
                                    password=password,
                                    email=email,
                                    default_project=default_project)
    # TODO(garcianavalon) expose the role as a config option
    role = _grant_role(keystone, '_member_', new_user, default_project)
    return new_user
    
def activate_user(user_id):
    keystone = fiwareclient()
    user = keystone.users.get(user_id)
    project = keystone.projects.update(user.default_project_id, enabled=True)
    user = keystone.users.update(user, enabled=True)
    return user

def change_password(user_email, new_password):
    keystone = fiwareclient()
    user = _find_user(keystone, email=user_email)
    user = keystone.users.update(user, password=new_password, enabled=True)
    return user

def check_user(name):
    keystone = fiwareclient()
    user = _find_user(keystone, name=name)
    return user

def check_email(email):
    keystone = fiwareclient()
    user = _find_user(keystone, email=email)
    return user

# ROLES AND PERMISSIONS
def role_get(request, role_id):
    #manager = fiwareclient().fiware_roles.roles
    manager = api.keystone.keystoneclient(request, admin=True).fiware_roles.roles
    return manager.get(role_id)

def role_list(request):
    #manager = fiwareclient().fiware_roles.roles
    manager = api.keystone.keystoneclient(request, admin=True).fiware_roles.roles
    return manager.list()

def role_create(request, name, is_editable=True, application=None, **kwargs):
    #manager = fiwareclient().fiware_roles.roles
    manager = api.keystone.keystoneclient(request, admin=True).fiware_roles.roles
    return manager.create(name=name,
                is_editable=is_editable,
                application=application,
                **kwargs)

def role_update(request, role, name=None, is_editable=True, 
                application=None, **kwargs):
    #manager = fiwareclient().fiware_roles.roles
    manager = api.keystone.keystoneclient(request, admin=True).fiware_roles.roles
    return manager.update(role, 
                        name=name,
                        is_editable=is_editable,
                        application=application,
                        **kwargs)
        
def role_delete(request, role_id):
    #manager = fiwareclient().fiware_roles.roles
    manager = api.keystone.keystoneclient(request, admin=True).fiware_roles.roles
    return manager.delete(role_id)

def permission_get(request, permission_id):
    #manager = fiwareclient().fiware_roles.permissions
    manager = api.keystone.keystoneclient(request, admin=True).fiware_roles.permissions
    return manager.get(permission_id)

def permission_list(request):
    #manager = fiwareclient().fiware_roles.permissions
    manager = api.keystone.keystoneclient(request, admin=True).fiware_roles.permissions
    return manager.list()

def permission_create(request, name, is_editable=True, application=None, **kwargs):
    #manager = fiwareclient().fiware_roles.permissions
    manager = api.keystone.keystoneclient(request, admin=True).fiware_roles.permissions
    return manager.create(name=name,
                is_editable=is_editable,
                application=application,
                **kwargs)

def permission_update(request, permission, name=None, is_editable=True, 
                application=None, **kwargs):
    #manager = fiwareclient().fiware_roles.permissions
    manager = api.keystone.keystoneclient(request, admin=True).fiware_roles.permissions
    return manager.update(permission, 
                        name=name,
                        is_editable=is_editable,
                        application=application,
                        **kwargs)
        
def permission_delete(request, permission_id):
    #manager = fiwareclient().fiware_roles.permissions
    manager = api.keystone.keystoneclient(request, admin=True).fiware_roles.permissions
    return manager.delete(permission_id)


# APPLICATIONS/CONSUMERS
def application_create(request, name, redirect_uris, scopes=['all_info'],
                    client_type='confidential', description=None, 
                    grant_type='authorization_code', extra=None):
    """ Registers a new consumer in the Keystone OAuth2 extension.

    In FIWARE applications is the name OAuth2 consumers/clients receive.
    """
    manager = api.keystone.keystoneclient(request, admin=True).oauth2.consumers
    return manager.create(name=name,
                        redirect_uris=redirect_uris,
                        description=description,
                        scopes=scopes,
                        client_type=client_type,
                        grant_type=grant_type,
                        extra=extra)

def application_list(request, user=None):
    manager = api.keystone.keystoneclient(request, admin=True).oauth2.consumers
    return manager.list(user=user)

def application_get(request, application_id, use_idm_account=False):
    if use_idm_account:
        manager = fiwareclient().oauth2.consumers
    else:
        manager = api.keystone.keystoneclient(request, admin=True).oauth2.consumers
    return manager.get(application_id)

def application_update(request, consumer_id, name=None, description=None, client_type=None, 
                redirect_uris=None, grant_type=None, scopes=None, **kwargs):
    manager = api.keystone.keystoneclient(request, admin=True).oauth2.consumers
    return manager.update(consumer=consumer_id,
                        name=name,
                        description=description,
                        client_type=client_type,
                        redirect_uris=redirect_uris,
                        grant_type=grant_type,
                        scopes=scopes,
                        **kwargs)

def application_delete(request, application_id):
    manager = api.keystone.keystoneclient(request, admin=True).oauth2.consumers
    return manager.delete(application_id)


# OAUTH2 FLOW
def request_authorization_for_application(request, application, 
                                        redirect_uri, scope=['all_info'], state=None):
    """ Sends the consumer/client credentials to the authorization server to ask
    a resource owner for authorization in a certain scope.

    :returns: a dict with all the data response from the provider, use it to populate
        a nice form for the user, for example.
    """
    LOG.debug('Requesting authorization for application: {0} with redirect_uri: {1} \
        and scope: {2} by user {3}'.format(application, redirect_uri, scope, request.user))
    manager = api.keystone.keystoneclient(request, admin=True).oauth2.authorization_codes
    response_dict = manager.request_authorization(consumer=application, 
                                    redirect_uri=redirect_uri, 
                                    scope=scope, 
                                    state=state)
    return  response_dict

def check_authorization_for_application(request, application, 
                                        redirect_uri, scope=['all_info']):
    """ Checks if the requesting application already got authorized by the user, so we don't
    need to make all the steps again. 

        The logic is that if the application already has a (valid) access token for that
    user and the scopes and redirect uris are registered then we can issue a new token for
    it.
    """
    LOG.debug('Checking if application {0} was already authorized by user {1}'.format(
                                                                application, request.user))
    manager = api.keystone.keystoneclient(request, admin=True).oauth2.access_tokens
    # FIXME(garcianavalon) the keystoneclient is not ready yet

def authorize_application(request, application, scopes=['all_info'], redirect=False):
    """ Give authorization from a resource owner to the consumer/client on the 
    requested scopes.

    Example use case: when the user is redirected from the application website to
    us, the provider/resource owner we present a nice form. If the user accepts, we
    delegate to our Keystone backend, where the client credentials will be checked an
    an authorization_code returned if everything is correct.

    :returns: an authorization_code object, following the same pattern as other 
        keystoneclient objects
    """
    LOG.debug('Authorizing application: {0} by user: {1}'.format(application, request.user))
    manager = api.keystone.keystoneclient(request, admin=True).oauth2.authorization_codes
    authorization_code = manager.authorize(
                                    consumer=application, 
                                    scopes=scopes, 
                                    redirect=redirect)
    return authorization_code

def obtain_access_token(request, consumer_id, consumer_secret, code,
               redirect_uri):
    """ Exchange the authorization_code for an access_token.

    This token can be later exchanged for a keystone scoped token using the oauth2
    auth method. See the Keystone OAuth2 Extension documentation for more information
    about the auth plugin.

    :returns: an access_token object
    """
    # NOTE(garcianavalon) right now this method has no use because is a wrapper for a
    # method intented to be use by the client/consumer. For the IdM is much more 
    # convenient to simply forward the request, see forward_access_token_request method
    LOG.debug('Exchanging code: {0} by application: {1}'.format(code, consumer_id))
    manager = fiwareclient().oauth2.access_tokens
    access_token = manager.create(consumer_id=consumer_id, 
                                consumer_secret=consumer_secret, 
                                authorization_code=code,
                                redirect_uri=redirect_uri)
    return access_token

def forward_access_token_request(request):
    """ Forwards the request to the keystone backend."""
    # TODO(garcianavalon) figure out if this method belongs to keystone client or if
    # there is a better way to do it/structure this
    headers = {
        'Authorization': request.META['HTTP_AUTHORIZATION'],
        'Content-Type': request.META['CONTENT_TYPE'],
    }
    body = request.body
    keystone_url = getattr(settings, 'OPENSTACK_KEYSTONE_URL') + '/OS-OAUTH2/access_token'
    LOG.debug('API_KEYSTONE: POST to {0} with body {1} and headers {2}'.format(keystone_url,
                                                                            body, headers))
    response = requests.post(keystone_url, data=body, headers=headers)
    return response

def login_with_oauth(request, access_token, project=None):
    """ Use an OAuth2 access token to obtain a keystone token, scoped for
    the authorizing user in one of his projects.
    """
    pass
    # TODO(garcianavalon) find out if we need this method
    # session = _oauth2_session(access_token, project_id=project)
    # return fiwareclient(session=session,request=request)

# FIWARE-IdM API CALLS

def forward_validate_token_request(request):
    """ Forwards the request to the keystone backend."""
    # TODO(garcianavalon) figure out if this method belongs to keystone client or if
    # there is a better way to do it/structure this
    keystone_url = getattr(settings, 'OPENSTACK_KEYSTONE_URL')
    endpoint = '/access-tokens/{0}'.format(request.GET.get('access_token'))
    url = keystone_url + endpoint
    LOG.debug('API_KEYSTONE: GET to {0}'.format(url))
    response = requests.get(url)
    return response