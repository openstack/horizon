# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 OpenStack Foundation
# Copyright 2012 Nebula, Inc.
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

import collections
import logging
from urllib import parse

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from keystoneauth1 import session
from keystoneauth1 import token_endpoint
from keystoneclient import exceptions as keystone_exceptions

from openstack_auth import backend
from openstack_auth import utils as auth_utils

from horizon import exceptions

from openstack_dashboard.api import base
from openstack_dashboard.contrib.developer.profiler import api as profiler
from openstack_dashboard import policy
from openstack_dashboard.utils import settings as setting_utils


LOG = logging.getLogger(__name__)
DEFAULT_ROLE = None
DEFAULT_DOMAIN = settings.OPENSTACK_KEYSTONE_DEFAULT_DOMAIN


# Set up our data structure for managing Identity API versions, and
# add a couple utility methods to it.
class IdentityAPIVersionManager(base.APIVersionManager):
    def upgrade_v2_user(self, user):
        if getattr(user, "project_id", None) is None:
            user.project_id = getattr(user, "default_project_id",
                                      getattr(user, "tenantId", None))
        return user

    def get_project_manager(self, *args, **kwargs):
        return keystoneclient(*args, **kwargs).projects


VERSIONS = IdentityAPIVersionManager(
    "identity", preferred_version=auth_utils.get_keystone_version())


try:
    # pylint: disable=ungrouped-imports
    from keystoneclient.v3 import client as keystone_client_v3
    VERSIONS.load_supported_version(3, {"client": keystone_client_v3})
except ImportError:
    pass


class Service(base.APIDictWrapper):
    """Wrapper for a dict based on the service data from keystone."""
    _attrs = ['id', 'type', 'name']

    def __init__(self, service, region, *args, **kwargs):
        super().__init__(service, *args, **kwargs)
        self.public_url = base.get_url_for_service(service, region,
                                                   'publicURL')
        self.url = base.get_url_for_service(service, region,
                                            settings.OPENSTACK_ENDPOINT_TYPE)
        if self.url:
            self.host = parse.urlparse(self.url).hostname
        else:
            self.host = None
        self.disabled = None
        self.region = region

    def __str__(self):
        if(self.type == "identity"):
            return _("%(type)s (%(backend)s backend)") \
                % {"type": self.type, "backend": keystone_backend_name()}
        return self.type

    def __repr__(self):
        return "<Service: %s>" % self


def _get_endpoint_url(request, endpoint_type, catalog=None):
    if getattr(request.user, "service_catalog", None):
        url = base.url_for(request,
                           service_type='identity',
                           endpoint_type=endpoint_type)
        message = ("The Keystone URL in service catalog points to a v2.0 "
                   "Keystone endpoint, but v3 is specified as the API version "
                   "to use by Horizon. Using v3 endpoint for authentication.")
    else:
        auth_url = settings.OPENSTACK_KEYSTONE_URL
        url = request.session.get('region_endpoint', auth_url)
        message = ("The OPENSTACK_KEYSTONE_URL setting points to a v2.0 "
                   "Keystone endpoint, but v3 is specified as the API version "
                   "to use by Horizon. Using v3 endpoint for authentication.")

    # TODO(gabriel): When the Service Catalog no longer contains API versions
    # in the endpoints this can be removed.
    url, url_fixed = auth_utils.fix_auth_url_version_prefix(url)
    if url_fixed:
        LOG.warning(message)

    return url


def keystoneclient(request, admin=False):
    """Returns a client connected to the Keystone backend.

    Several forms of authentication are supported:

        * Username + password -> Unscoped authentication
        * Username + password + tenant id -> Scoped authentication
        * Unscoped token -> Unscoped authentication
        * Unscoped token + tenant id -> Scoped authentication
        * Scoped token -> Scoped authentication

    Available services and data from the backend will vary depending on
    whether the authentication was scoped or unscoped.

    Lazy authentication if an ``endpoint`` parameter is provided.

    Calls requiring the admin endpoint should have ``admin=True`` passed in
    as a keyword argument.

    The client is cached so that subsequent API calls during the same
    request/response cycle don't have to be re-authenticated.
    """
    client_version = VERSIONS.get_active_version()
    user = request.user
    token_id = user.token.id

    if settings.OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT:
        is_domain_context_specified = bool(
            request.session.get("domain_context"))

        # If user is Cloud Admin, Domain Admin or Mixed Domain Admin and there
        # is no domain context specified, use domain scoped token
        if is_domain_admin(request) and not is_domain_context_specified:
            domain_token = request.session.get('domain_token')
            if domain_token:
                token_id = getattr(domain_token, 'auth_token', None)

    if admin:
        if not policy.check((("identity", "admin_required"),), request):
            raise exceptions.NotAuthorized
        endpoint_type = 'adminURL'
    else:
        endpoint_type = settings.OPENSTACK_ENDPOINT_TYPE

    # Take care of client connection caching/fetching a new client.
    # Admin vs. non-admin clients are cached separately for token matching.
    cache_attr = "_keystoneclient_admin" if admin \
        else backend.KEYSTONE_CLIENT_ATTR
    if (hasattr(request, cache_attr) and
        (not user.token.id or
         getattr(request, cache_attr).auth_token == user.token.id)):
        conn = getattr(request, cache_attr)
    else:
        endpoint = _get_endpoint_url(request, endpoint_type)
        verify = not settings.OPENSTACK_SSL_NO_VERIFY
        cacert = settings.OPENSTACK_SSL_CACERT
        verify = verify and cacert
        LOG.debug("Creating a new keystoneclient connection to %s.", endpoint)
        remote_addr = request.environ.get('REMOTE_ADDR', '')
        token_auth = token_endpoint.Token(endpoint=endpoint,
                                          token=token_id)
        keystone_session = session.Session(auth=token_auth,
                                           original_ip=remote_addr,
                                           verify=verify)
        conn = client_version['client'].Client(session=keystone_session,
                                               debug=settings.DEBUG)
        setattr(request, cache_attr, conn)
    return conn


@profiler.trace
def get_identity_api_version(request):
    client = keystoneclient(request)
    endpoint_data = client.session.get_endpoint_data(service_type='identity')
    return endpoint_data.api_version


@profiler.trace
def domain_create(request, name, description=None, enabled=None):
    manager = keystoneclient(request, admin=True).domains
    return manager.create(name=name,
                          description=description,
                          enabled=enabled)


@profiler.trace
def domain_get(request, domain_id):
    manager = keystoneclient(request, admin=True).domains
    return manager.get(domain_id)


@profiler.trace
def domain_delete(request, domain_id):
    manager = keystoneclient(request, admin=True).domains
    manager.delete(domain_id)


@profiler.trace
def domain_list(request):
    manager = keystoneclient(request, admin=True).domains
    return manager.list()


def domain_lookup(request):
    if policy.check((("identity", "identity:list_domains"),), request) \
            and request.session.get('domain_token'):
        try:
            domains = domain_list(request)
            return dict((d.id, d.name) for d in domains)
        except Exception:
            LOG.warning("Pure project admin doesn't have a domain token")
            return {}
    else:
        domain = get_default_domain(request)
        return {domain.id: domain.name}


@profiler.trace
def domain_update(request, domain_id, name=None, description=None,
                  enabled=None):
    manager = keystoneclient(request, admin=True).domains
    try:
        response = manager.update(domain_id, name=name,
                                  description=description, enabled=enabled)
    except Exception:
        LOG.exception("Unable to update Domain: %s", domain_id)
        raise
    return response


@profiler.trace
def tenant_create(request, name, description=None, enabled=None,
                  domain=None, **kwargs):
    manager = VERSIONS.get_project_manager(request, admin=True)
    try:
        return manager.create(name, domain,
                              description=description,
                              enabled=enabled, **kwargs)
    except keystone_exceptions.Conflict:
        raise exceptions.Conflict()


def get_default_domain(request, get_name=True):
    """Gets the default domain object to use when creating Identity object.

    Returns the domain context if is set, otherwise return the domain
    of the logon user.

    :param get_name: Whether to get the domain name from Keystone if the
        context isn't set.  Setting this to False prevents an unnecessary call
        to Keystone if only the domain ID is needed.
    """
    domain_id = request.session.get("domain_context", None)
    domain_name = request.session.get("domain_context_name", None)
    if domain_id is None:
        # if no domain context set, default to user's domain
        domain_id = request.user.user_domain_id
        domain_name = request.user.user_domain_name
        if get_name and not request.user.is_federated:
            try:
                domain = domain_get(request, domain_id)
                domain_name = domain.name
            except exceptions.NotAuthorized:
                # NOTE (knasim-wrs): Retrieving domain information
                # is an admin URL operation. As a pre-check, such
                # operations would be Forbidden if the logon user does
                # not have an 'admin' role on the current project.
                #
                # Since this can be a common occurence and can cause
                # incessant warning logging in the horizon logs,
                # we recognize this condition and return the user's
                # domain information instead.
                LOG.debug("Cannot retrieve domain information for "
                          "user (%(user)s) that does not have an admin role "
                          "on project (%(project)s)",
                          {'user': request.user.username,
                           'project': request.user.project_name})
            except Exception:
                LOG.warning("Unable to retrieve Domain: %s", domain_id)
    domain = base.APIDictWrapper({"id": domain_id,
                                  "name": domain_name})
    return domain


def get_effective_domain_id(request):
    """Gets the id of the default domain.

    If the requests default domain is the same as DEFAULT_DOMAIN,
    return None.
    """
    default_domain = get_default_domain(request)
    domain_id = default_domain.get('id')
    domain_name = default_domain.get('name')
    return None if domain_name == DEFAULT_DOMAIN else domain_id


def is_cloud_admin(request):
    return policy.check((("identity", "cloud_admin"),), request)


def is_domain_admin(request):
    return policy.check(
        (("identity", "admin_and_matching_domain_id"),), request)


# TODO(gabriel): Is there ever a valid case for admin to be false here?
# A quick search through the codebase reveals that it's always called with
# admin=true so I suspect we could eliminate it entirely as with the other
# tenant commands.
@profiler.trace
def tenant_get(request, project, admin=True):
    manager = VERSIONS.get_project_manager(request, admin=admin)
    try:
        return manager.get(project)
    except keystone_exceptions.NotFound:
        LOG.info("Tenant '%s' not found.", project)
        raise


@profiler.trace
def tenant_delete(request, project):
    manager = VERSIONS.get_project_manager(request, admin=True)
    manager.delete(project)


@profiler.trace
def tenant_list(request, paginate=False, marker=None, domain=None, user=None,
                admin=True, filters=None):
    manager = VERSIONS.get_project_manager(request, admin=admin)
    tenants = []
    has_more_data = False

    # if requesting the projects for the current user,
    # return the list from the cache
    if user == request.user.id:
        tenants = request.user.authorized_tenants
    else:
        domain_id = get_effective_domain_id(request)
        kwargs = {
            "domain": domain_id,
            "user": user
        }
        if filters is not None:
            kwargs.update(filters)
        if 'id' in kwargs:
            try:
                tenants = [tenant_get(request, kwargs['id'])]
            except keystone_exceptions.NotFound:
                tenants = []
            except Exception:
                exceptions.handle(request)
        else:
            tenants = manager.list(**kwargs)
    return tenants, has_more_data


@profiler.trace
def tenant_update(request, project, name=None, description=None,
                  enabled=None, domain=None, **kwargs):
    manager = VERSIONS.get_project_manager(request, admin=True)
    try:
        return manager.update(project, name=name, description=description,
                              enabled=enabled, domain=domain, **kwargs)
    except keystone_exceptions.Conflict:
        raise exceptions.Conflict()


@profiler.trace
def user_list(request, project=None, domain=None, group=None, filters=None):
    users = []
    kwargs = {
        "project": project,
        "domain": domain,
        "group": group
    }
    if filters is not None:
        kwargs.update(filters)
    if 'id' in kwargs:
        try:
            users = [user_get(request, kwargs['id'])]
        except keystone_exceptions.NotFound:
            raise exceptions.NotFound()
    else:
        users = keystoneclient(request, admin=True).users.list(**kwargs)
    return [VERSIONS.upgrade_v2_user(user) for user in users]


@profiler.trace
def user_create(request, name=None, email=None, password=None, project=None,
                enabled=None, domain=None, description=None, **data):
    manager = keystoneclient(request, admin=True).users
    try:
        return manager.create(name, password=password, email=email,
                              default_project=project, enabled=enabled,
                              domain=domain, description=description,
                              **data)
    except keystone_exceptions.Conflict:
        raise exceptions.Conflict()


@profiler.trace
def user_delete(request, user_id):
    keystoneclient(request, admin=True).users.delete(user_id)


@profiler.trace
def user_get(request, user_id, admin=True):
    user = keystoneclient(request, admin=admin).users.get(user_id)
    return VERSIONS.upgrade_v2_user(user)


@profiler.trace
def user_update(request, user, **data):
    manager = keystoneclient(request, admin=True).users

    if not keystone_can_edit_user():
        raise keystone_exceptions.ClientException(
            _("Identity service does not allow editing user data."))
    try:
        user = manager.update(user, **data)
    except keystone_exceptions.Conflict:
        raise exceptions.Conflict()


@profiler.trace
def user_update_enabled(request, user, enabled):
    manager = keystoneclient(request, admin=True).users
    manager.update(user, enabled=enabled)


@profiler.trace
def user_update_password(request, user, password, admin=True):

    if not keystone_can_edit_user():
        raise keystone_exceptions.ClientException(
            _("Identity service does not allow editing user password."))

    manager = keystoneclient(request, admin=admin).users
    manager.update(user, password=password)


def user_verify_admin_password(request, admin_password):
    # attempt to create a new client instance with admin password to
    # verify if it's correct.
    client = keystone_client_v3
    try:
        endpoint = _get_endpoint_url(request, 'publicURL')
        insecure = settings.OPENSTACK_SSL_NO_VERIFY
        cacert = settings.OPENSTACK_SSL_CACERT
        client.Client(
            username=request.user.username,
            password=admin_password,
            insecure=insecure,
            cacert=cacert,
            auth_url=endpoint
        )
        return True
    except Exception:
        exceptions.handle(request, ignore=True)
        return False


@profiler.trace
def user_update_own_password(request, origpassword, password):
    client = keystoneclient(request, admin=False)
    client.users.client.session.auth.user_id = request.user.id
    return client.users.update_password(origpassword, password)


@profiler.trace
def user_update_tenant(request, user, project, admin=True):
    manager = keystoneclient(request, admin=admin).users
    return manager.update(user, project=project)


@profiler.trace
def group_create(request, domain_id, name, description=None):
    manager = keystoneclient(request, admin=True).groups
    try:
        return manager.create(domain=domain_id,
                              name=name,
                              description=description)
    except keystone_exceptions.Conflict:
        raise exceptions.Conflict()


@profiler.trace
def group_get(request, group_id, admin=True):
    manager = keystoneclient(request, admin=admin).groups
    return manager.get(group_id)


@profiler.trace
def group_delete(request, group_id):
    manager = keystoneclient(request, admin=True).groups
    return manager.delete(group_id)


@profiler.trace
def group_list(request, domain=None, project=None, user=None, filters=None):
    manager = keystoneclient(request, admin=True).groups
    groups = []
    kwargs = {
        "domain": domain,
        "user": user,
        "name": None
    }
    if filters is not None:
        kwargs.update(filters)
    if 'id' in kwargs:
        try:
            groups = [manager.get(kwargs['id'])]
        except keystone_exceptions.NotFound:
            raise exceptions.NotFound()
    else:
        groups = manager.list(**kwargs)

    if project:
        project_groups = []
        for group in groups:
            roles = roles_for_group(request, group=group.id, project=project)
            if roles:
                project_groups.append(group)
        groups = project_groups
    return groups


@profiler.trace
def group_update(request, group_id, name=None, description=None):
    manager = keystoneclient(request, admin=True).groups
    try:
        return manager.update(group=group_id,
                              name=name,
                              description=description)
    except keystone_exceptions.Conflict:
        raise exceptions.Conflict()


@profiler.trace
def add_group_user(request, group_id, user_id):
    manager = keystoneclient(request, admin=True).users
    return manager.add_to_group(group=group_id, user=user_id)


@profiler.trace
def remove_group_user(request, group_id, user_id):
    manager = keystoneclient(request, admin=True).users
    return manager.remove_from_group(group=group_id, user=user_id)


def get_project_groups_roles(request, project):
    """Gets the groups roles in a given project.

    :param request: the request entity containing the login user information
    :param project: the project to filter the groups roles. It accepts both
                    project object resource or project ID

    :returns group_roles: a dictionary mapping the groups and their roles in
                          given project

    """
    groups_roles = collections.defaultdict(list)
    project_role_assignments = role_assignments_list(request,
                                                     project=project)

    for role_assignment in project_role_assignments:
        if not hasattr(role_assignment, 'group'):
            continue
        group_id = role_assignment.group['id']
        role_id = role_assignment.role['id']

        # filter by project_id
        if ('project' in role_assignment.scope and
                role_assignment.scope['project']['id'] == project):
            groups_roles[group_id].append(role_id)
    return groups_roles


@profiler.trace
def role_assignments_list(request, project=None, user=None, role=None,
                          group=None, domain=None, effective=False,
                          include_subtree=True, include_names=False):
    if include_subtree:
        domain = None

    manager = keystoneclient(request, admin=True).role_assignments

    return manager.list(project=project, user=user, role=role, group=group,
                        domain=domain, effective=effective,
                        include_subtree=include_subtree,
                        include_names=include_names)


@profiler.trace
def role_create(request, name):
    manager = keystoneclient(request, admin=True).roles
    return manager.create(name)


@profiler.trace
def role_get(request, role_id):
    manager = keystoneclient(request, admin=True).roles
    return manager.get(role_id)


@profiler.trace
def role_update(request, role_id, name=None):
    manager = keystoneclient(request, admin=True).roles
    return manager.update(role_id, name)


@profiler.trace
def role_delete(request, role_id):
    manager = keystoneclient(request, admin=True).roles
    manager.delete(role_id)


@profiler.trace
def role_list(request, filters=None):
    """Returns a global list of available roles."""
    manager = keystoneclient(request, admin=True).roles
    roles = []
    kwargs = {}
    if filters is not None:
        kwargs.update(filters)
    if 'id' in kwargs:
        try:
            roles = [manager.get(kwargs['id'])]
        except keystone_exceptions.NotFound:
            roles = []
        except Exception:
            exceptions.handle(request)
    else:
        roles = manager.list(**kwargs)
    return roles


@profiler.trace
def roles_for_user(request, user, project=None, domain=None):
    """Returns a list of user roles scoped to a project or domain."""
    manager = keystoneclient(request, admin=True).roles
    return manager.list(user=user, domain=domain, project=project)


@profiler.trace
def get_domain_users_roles(request, domain):
    users_roles = collections.defaultdict(list)
    domain_role_assignments = role_assignments_list(request,
                                                    domain=domain,
                                                    include_subtree=False)
    for role_assignment in domain_role_assignments:
        if not hasattr(role_assignment, 'user'):
            continue
        user_id = role_assignment.user['id']
        role_id = role_assignment.role['id']

        # filter by domain_id
        if ('domain' in role_assignment.scope and
                role_assignment.scope['domain']['id'] == domain):
            users_roles[user_id].append(role_id)
    return users_roles


@profiler.trace
def add_domain_user_role(request, user, role, domain):
    """Adds a role for a user on a domain."""
    manager = keystoneclient(request, admin=True).roles
    return manager.grant(role, user=user, domain=domain)


@profiler.trace
def remove_domain_user_role(request, user, role, domain=None):
    """Removes a given single role for a user from a domain."""
    manager = keystoneclient(request, admin=True).roles
    return manager.revoke(role, user=user, domain=domain)


@profiler.trace
def get_project_users_roles(request, project):
    users_roles = collections.defaultdict(list)
    project_role_assignments = role_assignments_list(request,
                                                     project=project)
    for role_assignment in project_role_assignments:
        if not hasattr(role_assignment, 'user'):
            continue
        user_id = role_assignment.user['id']
        role_id = role_assignment.role['id']

        # filter by project_id
        if ('project' in role_assignment.scope and
                role_assignment.scope['project']['id'] == project):
            users_roles[user_id].append(role_id)
    return users_roles


@profiler.trace
def add_tenant_user_role(request, project=None, user=None, role=None,
                         group=None, domain=None):
    """Adds a role for a user on a tenant."""
    manager = keystoneclient(request, admin=True).roles
    manager.grant(role, user=user, project=project,
                  group=group, domain=domain)


@profiler.trace
def remove_tenant_user_role(request, project=None, user=None, role=None,
                            group=None, domain=None):
    """Removes a given single role for a user from a tenant."""
    manager = keystoneclient(request, admin=True).roles
    return manager.revoke(role, user=user, project=project,
                          group=group, domain=domain)


def remove_tenant_user(request, project=None, user=None, domain=None):
    """Removes all roles from a user on a tenant, removing them from it."""
    client = keystoneclient(request, admin=True)
    roles = client.roles.roles_for_user(user, project)
    for role in roles:
        remove_tenant_user_role(request, user=user, role=role.id,
                                project=project, domain=domain)


@profiler.trace
def roles_for_group(request, group, domain=None, project=None):
    manager = keystoneclient(request, admin=True).roles
    return manager.list(group=group, domain=domain, project=project)


@profiler.trace
def add_group_role(request, role, group, domain=None, project=None):
    """Adds a role for a group on a domain or project."""
    manager = keystoneclient(request, admin=True).roles
    return manager.grant(role=role, group=group, domain=domain,
                         project=project)


@profiler.trace
def remove_group_role(request, role, group, domain=None, project=None):
    """Removes a given single role for a group from a domain or project."""
    manager = keystoneclient(request, admin=True).roles
    return manager.revoke(role=role, group=group, project=project,
                          domain=domain)


@profiler.trace
def remove_group_roles(request, group, domain=None, project=None):
    """Removes all roles from a group on a domain or project."""
    client = keystoneclient(request, admin=True)
    roles = client.roles.list(group=group, domain=domain, project=project)
    for role in roles:
        remove_group_role(request, role=role.id, group=group,
                          domain=domain, project=project)


def get_default_role(request):
    """Gets the default role object from Keystone and saves it as a global.

    Since this is configured in settings and should not change from request
    to request. Supports lookup by name or id.
    """
    global DEFAULT_ROLE
    default = settings.OPENSTACK_KEYSTONE_DEFAULT_ROLE
    if default and DEFAULT_ROLE is None:
        try:
            roles = keystoneclient(request, admin=True).roles.list()
        except Exception:
            roles = []
            exceptions.handle(request)
        for role in roles:
            if default in (role.id, role.name):
                DEFAULT_ROLE = role
                break
    return DEFAULT_ROLE


def ec2_manager(request):
    client = keystoneclient(request)
    if hasattr(client, 'ec2'):
        return client.ec2

    from keystoneclient.v3 import ec2
    return ec2.EC2Manager(client)


@profiler.trace
def list_ec2_credentials(request, user_id):
    return ec2_manager(request).list(user_id)


@profiler.trace
def create_ec2_credentials(request, user_id, tenant_id):
    return ec2_manager(request).create(user_id, tenant_id)


@profiler.trace
def get_user_ec2_credentials(request, user_id, access_token):
    return ec2_manager(request).get(user_id, access_token)


@profiler.trace
def delete_user_ec2_credentials(request, user_id, access_token):
    return ec2_manager(request).delete(user_id, access_token)


def keystone_can_edit_domain():
    can_edit_domain = setting_utils.get_dict_config(
        'OPENSTACK_KEYSTONE_BACKEND', 'can_edit_domain')
    multi_domain_support = settings.OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT
    return can_edit_domain and multi_domain_support


def keystone_can_edit_user():
    return setting_utils.get_dict_config(
        'OPENSTACK_KEYSTONE_BACKEND', 'can_edit_user')


def keystone_can_edit_project():
    return setting_utils.get_dict_config(
        'OPENSTACK_KEYSTONE_BACKEND', 'can_edit_project')


def keystone_can_edit_group():
    return setting_utils.get_dict_config(
        'OPENSTACK_KEYSTONE_BACKEND', 'can_edit_group')


def keystone_can_edit_role():
    return setting_utils.get_dict_config(
        'OPENSTACK_KEYSTONE_BACKEND', 'can_edit_role')


def keystone_backend_name():
    return setting_utils.get_dict_config(
        'OPENSTACK_KEYSTONE_BACKEND', 'name') or 'unknown'


def get_version():
    return VERSIONS.active


def identity_provider_create(request, idp_id, description=None,
                             enabled=False, remote_ids=None):
    manager = keystoneclient(request, admin=True).federation.identity_providers
    try:
        return manager.create(id=idp_id,
                              description=description,
                              enabled=enabled,
                              remote_ids=remote_ids)
    except keystone_exceptions.Conflict:
        raise exceptions.Conflict()


@profiler.trace
def identity_provider_get(request, idp_id):
    manager = keystoneclient(request, admin=True).federation.identity_providers
    return manager.get(idp_id)


@profiler.trace
def identity_provider_update(request, idp_id, description=None,
                             enabled=False, remote_ids=None):
    manager = keystoneclient(request, admin=True).federation.identity_providers
    try:
        return manager.update(idp_id,
                              description=description,
                              enabled=enabled,
                              remote_ids=remote_ids)
    except keystone_exceptions.Conflict:
        raise exceptions.Conflict()


@profiler.trace
def identity_provider_delete(request, idp_id):
    manager = keystoneclient(request, admin=True).federation.identity_providers
    return manager.delete(idp_id)


@profiler.trace
def identity_provider_list(request):
    manager = keystoneclient(request, admin=True).federation.identity_providers
    return manager.list()


@profiler.trace
def mapping_create(request, mapping_id, rules):
    manager = keystoneclient(request, admin=True).federation.mappings
    try:
        return manager.create(mapping_id=mapping_id, rules=rules)
    except keystone_exceptions.Conflict:
        raise exceptions.Conflict()


@profiler.trace
def mapping_get(request, mapping_id):
    manager = keystoneclient(request, admin=True).federation.mappings
    return manager.get(mapping_id)


@profiler.trace
def mapping_update(request, mapping_id, rules):
    manager = keystoneclient(request, admin=True).federation.mappings
    return manager.update(mapping_id, rules=rules)


@profiler.trace
def mapping_delete(request, mapping_id):
    manager = keystoneclient(request, admin=True).federation.mappings
    return manager.delete(mapping_id)


@profiler.trace
def mapping_list(request):
    manager = keystoneclient(request, admin=True).federation.mappings
    return manager.list()


@profiler.trace
def protocol_create(request, protocol_id, identity_provider, mapping):
    manager = keystoneclient(request).federation.protocols
    try:
        return manager.create(protocol_id, identity_provider, mapping)
    except keystone_exceptions.Conflict:
        raise exceptions.Conflict()


@profiler.trace
def protocol_get(request, identity_provider, protocol):
    manager = keystoneclient(request).federation.protocols
    return manager.get(identity_provider, protocol)


@profiler.trace
def protocol_update(request, identity_provider, protocol, mapping):
    manager = keystoneclient(request).federation.protocols
    return manager.update(identity_provider, protocol, mapping)


@profiler.trace
def protocol_delete(request, identity_provider, protocol):
    manager = keystoneclient(request).federation.protocols
    return manager.delete(identity_provider, protocol)


@profiler.trace
def protocol_list(request, identity_provider):
    manager = keystoneclient(request).federation.protocols
    return manager.list(identity_provider)


@profiler.trace
def application_credential_list(request, filters=None):
    user = request.user.id
    manager = keystoneclient(request).application_credentials
    return manager.list(user=user, **filters)


@profiler.trace
def application_credential_get(request, application_credential_id):
    user = request.user.id
    manager = keystoneclient(request).application_credentials
    return manager.get(application_credential=application_credential_id,
                       user=user)


@profiler.trace
def application_credential_delete(request, application_credential_id):
    user = request.user.id
    manager = keystoneclient(request).application_credentials
    return manager.delete(application_credential=application_credential_id,
                          user=user)


@profiler.trace
def application_credential_create(request, name, secret=None,
                                  description=None, expires_at=None,
                                  roles=None, unrestricted=False,
                                  access_rules=None):
    user = request.user.id
    manager = keystoneclient(request).application_credentials
    try:
        return manager.create(name=name, user=user, secret=secret,
                              description=description, expires_at=expires_at,
                              roles=roles, unrestricted=unrestricted,
                              access_rules=access_rules)
    except keystone_exceptions.Conflict:
        raise exceptions.Conflict()
