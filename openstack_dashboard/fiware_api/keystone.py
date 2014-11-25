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

# TODO(garcianavalon) for now, the way we handle the fact that we are using
# a custom keystoneclient is by adding the package as a git submodule and
# importing it right here while we keep the default keystoneclient as a
# dependency. In the future and prior to relase we have to remove the
# default keystoneclient dependency in requirements.txt and install globally
# (in .venv/lib/pythonx.y/site_packages/keystoneclient or whatever folder in
# PYTHONPATH we want) the custom keystoneclient (aka fiwareclient) so it's the
# ony one used in the whole project
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
    default_project = keystone.projects.create(name, domain=default_domain)
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
# TODO(garcianavalon) we are using the idm account to create the roles instead
# of the current user account. To fix this we need first to solve the multiple
# keystoneclients issue (see the top of this file). 
# NOTE(garcianavalon) request is passed as an argument
# looking into the future integration, no use for it now
def role_get(request, role):
    manager = fiwareclient().fiware_roles.roles
    #manager = api.keystone.keystoneclient(request, admin=True).fiware_roles
    return manager.get(role)

def role_list(request):
    manager = fiwareclient().fiware_roles.roles
    #manager = api.keystone.keystoneclient(request, admin=True).fiware_roles
    return manager.list()

def role_create(request, name, is_editable=True, application=None, **kwargs):
    manager = fiwareclient().fiware_roles.roles
    #manager = api.keystone.keystoneclient(request, admin=True).fiware_roles
    return manager.create(name=name,
                is_editable=is_editable,
                application=application,
                **kwargs)

def role_update(request, role, name=None, is_editable=True, 
                application=None, **kwargs):
    manager = fiwareclient().fiware_roles.roles
    #manager = api.keystone.keystoneclient(request, admin=True).fiware_roles
    return manager.update(role, 
                        name=name,
                        is_editable=is_editable,
                        application=application,
                        **kwargs)
        
def role_delete(request, role):
    manager = fiwareclient().fiware_roles.roles
    #manager = api.keystone.keystoneclient(request, admin=True).fiware_roles
    return manager.delete(role)

def permission_get(request, permission):
    manager = fiwareclient().fiware_roles.permissions
    #manager = api.keystone.keystoneclient(request, admin=True).fiware_roles
    return manager.get(permission)

def permission_list(request):
    manager = fiwareclient().fiware_roles.permissions
    #manager = api.keystone.keystoneclient(request, admin=True).fiware_roles
    return manager.list()

def permission_create(request, name, is_editable=True, application=None, **kwargs):
    manager = fiwareclient().fiware_roles.permissions
    #manager = api.keystone.keystoneclient(request, admin=True).fiware_roles
    return manager.create(name=name,
                is_editable=is_editable,
                application=application,
                **kwargs)

def permission_update(request, permission, name=None, is_editable=True, 
                application=None, **kwargs):
    manager = fiwareclient().fiware_roles.permissions
    #manager = api.keystone.keystoneclient(request, admin=True).fiware_roles
    return manager.update(permission, 
                        name=name,
                        is_editable=is_editable,
                        application=application,
                        **kwargs)
        
def permission_delete(request, permission):
    manager = fiwareclient().fiware_roles.permissions
    #manager = api.keystone.keystoneclient(request, admin=True).fiware_roles
    return manager.delete(permission)


# APPLICATIONS/CONSUMERS
def application_create(request, name, redirect_uris, scopes=['all_info'],
                    client_type='confidential', description=None, 
                    grant_type='authorization_code', extra=None):
    """ Registers a new consumer in the Keystone OAuth2 extension.

    In FIWARE applications is the name OAuth2 consumers/clients receive.
    """
    manager = fiwareclient().oauth2.consumers
    return manager.create(name=name,
                        redirect_uris=redirect_uris,
                        description=description,
                        scopes=scopes,
                        client_type=client_type,
                        grant_type=grant_type,
                        extra=extra)

def application_list(request, user=None):
    manager = fiwareclient().oauth2.consumers
    return manager.list(user=user)

def application_get(request, application):
    manager = fiwareclient().oauth2.consumers
    return manager.get(application)



# OAUTH2 FLOW
def request_authorization_for_application(request, application, 
                                        redirect_uri, scope, state=None):
    """ Sends the consumer/client credentials to the authorization server to ask
    a resource owner for authorization in a certain scope.

    :returns: a dict with all the data response from the provider, use it to populate
        a nice form for the user, for example.
    """
    manager = fiwareclient(request).oauh2.authorization_codes
    response_dict = manager.request_authorization(consumer=application, 
                                    redirect_uri=redirect_uri, 
                                    scope=scope, 
                                    state=state)
    return  response_dict

def authorize_application(request, user, application, scopes, redirect=False):
    """ Give authorization from a resource owner to the consumer/client on the 
    requested scopes.

    Example use case: when the user is redirected from the application website to
    us, the provider/resource owner we present a nice form. If the user accepts, we
    delegate to our Keystone backend, where the client credentials will be checked an
    an authorization_code returned if everything is correct.

    :returns: an authorization_code object, following the same pattern as other 
        keystoneclient objects
    """
    manager = fiwareclient(request).oauth2.authorization_codes
    authorization_code = manager.authorize(user=user, 
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
    manager = fiwareclient(request).oauth2.access_tokens
    access_token = manager.create(consumer_id=consumer_id, 
                                consumer_secret=consumer_secret, 
                                authorization_code=code,
                                redirect_uri=redirect_uri)
    return access_token

def login_with_oauth(request, access_token, project=None):
    """ Use an OAuth2 access token to obtain a keystone token, scoped for
    the authorizing user in one of his projects.
    """
    pass
    # TODO(garcianavalon) find out if we need this method
    # session = _oauth2_session(access_token, project_id=project)
    # return fiwareclient(session=session,request=request)
