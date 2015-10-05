# Copyright 2014, Rackspace, US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""API over the keystone service.
"""

import django.http
from django.views import generic

from openstack_dashboard import api
from openstack_dashboard.api.rest import utils as rest_utils

from openstack_dashboard.api.rest import urls


@urls.register
class Version(generic.View):
    """API for active keystone version.
    """
    url_regex = r'keystone/version/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get active keystone version.
        """
        return {'version': api.keystone.get_version()}


@urls.register
class Users(generic.View):
    """API for keystone users.
    """
    url_regex = r'keystone/users/$'
    client_keywords = {'project_id', 'domain_id', 'group_id'}

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of users.

        By default, a listing of all users for the current domain are
        returned. You may specify GET parameters for project_id, domain_id and
        group_id to change that listing's context.

        The listing result is an object with property "items".
        """
        domain_context = request.session.get('domain_context')

        filters = rest_utils.parse_filters_kwargs(request,
                                                  self.client_keywords)[0]
        if len(filters) == 0:
            filters = None

        result = api.keystone.user_list(
            request,
            project=request.GET.get('project_id'),
            domain=request.GET.get('domain_id', domain_context),
            group=request.GET.get('group_id'),
            filters=filters
        )
        return {'items': [u.to_dict() for u in result]}

    @rest_utils.ajax(data_required=True)
    def post(self, request):
        """Create a user.

        Create a user using the parameters supplied in the POST
        application/json object. The base parameters are name (string), email
        (string, optional), password (string, optional), project_id (string,
        optional), enabled (boolean, defaults to true). The user will be
        created in the default domain.

        This action returns the new user object on success.
        """
        # not sure why email is forced to None, but other code does it
        domain = api.keystone.get_default_domain(request)
        new_user = api.keystone.user_create(
            request,
            name=request.DATA['name'],
            email=request.DATA.get('email') or None,
            password=request.DATA.get('password'),
            project=request.DATA.get('project_id') or None,
            enabled=True,
            domain=domain.id
        )

        return rest_utils.CreatedResponse(
            '/api/keystone/users/%s' % new_user.id,
            new_user.to_dict()
        )

    @rest_utils.ajax(data_required=True)
    def delete(self, request):
        """Delete multiple users by id.

        The DELETE data should be an application/json array of user ids to
        delete.

        This method returns HTTP 204 (no content) on success.
        """
        for user_id in request.DATA:
            if user_id != request.user.id:
                api.keystone.user_delete(request, user_id)


@urls.register
class User(generic.View):
    """API for a single keystone user.
    """
    url_regex = r'keystone/users/(?P<id>[0-9a-f]+|current)$'

    @rest_utils.ajax()
    def get(self, request, id):
        """Get a specific user by id.

        If the id supplied is 'current' then the current logged-in user
        will be returned, otherwise the user specified by the id.
        """
        if id == 'current':
            id = request.user.id
        return api.keystone.user_get(request, id).to_dict()

    @rest_utils.ajax()
    def delete(self, request, id):
        """Delete a single user by id.

        This method returns HTTP 204 (no content) on success.
        """
        if id == 'current':
            raise django.http.HttpResponseNotFound('current')
        api.keystone.user_delete(request, id)

    @rest_utils.ajax(data_required=True)
    def patch(self, request, id):
        """Update a single user.

        The PATCH data should be an application/json object with attributes to
        set to new values: password (string), project (string),
        enabled (boolean).

        A PATCH may contain any one of those attributes, but
        if it contains more than one it must contain the project, even
        if it is not being altered.

        This method returns HTTP 204 (no content) on success.
        """
        keys = tuple(request.DATA)
        user = api.keystone.user_get(request, id)

        if 'password' in keys:
            password = request.DATA['password']
            api.keystone.user_update_password(request, user, password)

        elif 'enabled' in keys:
            enabled = request.DATA['enabled']
            api.keystone.user_update_enabled(request, user, enabled)

        else:
            # note that project is actually project_id
            # but we can not rename due to legacy compatibility
            # refer to keystone.api user_update method
            api.keystone.user_update(request, user, **request.DATA)


@urls.register
class Roles(generic.View):
    """API over all roles.
    """
    url_regex = r'keystone/roles/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of roles.

        By default a listing of all roles are returned.

        If the GET parameters project_id and user_id are specified then that
        user's roles for that project are returned. If user_id is 'current'
        then the current user's roles for that project are returned.

        The listing result is an object with property "items".
        """
        project_id = request.GET.get('project_id')
        user_id = request.GET.get('user_id')
        if project_id and user_id:
            if user_id == 'current':
                user_id = request.user.id
            roles = api.keystone.roles_for_user(request, user_id,
                                                project_id) or []
            items = [r.to_dict() for r in roles]
        else:
            items = [r.to_dict() for r in api.keystone.role_list(request)]
        return {'items': items}

    @rest_utils.ajax(data_required=True)
    def post(self, request):
        """Create a role.

        Create a role using the "name" (string) parameter supplied in the POST
        application/json object.

        This method returns the new role object on success.
        """
        new_role = api.keystone.role_create(request, request.DATA['name'])
        return rest_utils.CreatedResponse(
            '/api/keystone/roles/%s' % new_role.id,
            new_role.to_dict()
        )

    @rest_utils.ajax(data_required=True)
    def delete(self, request):
        """Delete multiple roles by id.

        The DELETE data should be an application/json array of role ids to
                delete.

        This method returns HTTP 204 (no content) on success.
        """
        for role_id in request.DATA:
            api.keystone.role_delete(request, role_id)


@urls.register
class Role(generic.View):
    """API for a single role.
    """
    url_regex = r'keystone/roles/(?P<id>[0-9a-f]+|default)$'

    @rest_utils.ajax()
    def get(self, request, id):
        """Get a specific role by id.

        If the id supplied is 'default' then the default role will be
        returned, otherwise the role specified by the id.
        """
        if id == 'default':
            return api.keystone.get_default_role(request).to_dict()
        return api.keystone.role_get(request, id).to_dict()

    @rest_utils.ajax()
    def delete(self, request, id):
        """Delete a single role by id.

        This method returns HTTP 204 (no content) on success.
        """
        if id == 'default':
            raise django.http.HttpResponseNotFound('default')
        api.keystone.role_delete(request, id)

    @rest_utils.ajax(data_required=True)
    def patch(self, request, id):
        """Update a single role.

        The PATCH data should be an application/json object with the "name"
        attribute to update.

        This method returns HTTP 204 (no content) on success.
        """
        api.keystone.role_update(request, id, request.DATA['name'])


@urls.register
class Domains(generic.View):
    """API over all domains.
    """
    url_regex = r'keystone/domains/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of domains.

        A listing of all domains are returned.

        The listing result is an object with property "items".
        """
        items = [d.to_dict() for d in api.keystone.domain_list(request)]
        return {'items': items}

    @rest_utils.ajax(data_required=True)
    def post(self, request):
        """Perform some action on the collection of domains.

        This action creates a domain using parameters supplied in the POST
        application/json object. The "name" (string) parameter is required,
        others are optional: "description" (string) and "enabled" (boolean,
        defaults to true).

        This method returns the new domain object on success.
        """
        new_domain = api.keystone.domain_create(
            request,
            request.DATA['name'],
            description=request.DATA.get('description'),
            enabled=request.DATA.get('enabled', True),
        )
        return rest_utils.CreatedResponse(
            '/api/keystone/domains/%s' % new_domain.id,
            new_domain.to_dict()
        )

    @rest_utils.ajax(data_required=True)
    def delete(self, request):
        """Delete multiple domains by id.

        The DELETE data should be an application/json array of domain ids to
                delete.

        This method returns HTTP 204 (no content) on success.
        """
        for domain_id in request.DATA:
            api.keystone.domain_delete(request, domain_id)


@urls.register
class Domain(generic.View):
    """API over a single domains.
    """
    url_regex = r'keystone/domains/(?P<id>[0-9a-f]+|default)$'

    @rest_utils.ajax()
    def get(self, request, id):
        """Get a specific domain by id.

        If the id supplied is 'default' then the default domain will be
        returned, otherwise the domain specified by the id.
        """
        if id == 'default':
            return api.keystone.get_default_domain(request).to_dict()
        return api.keystone.domain_get(request, id).to_dict()

    @rest_utils.ajax()
    def delete(self, request, id):
        """Delete a single domain by id.

        This method returns HTTP 204 (no content) on success.
        """
        if id == 'default':
            raise django.http.HttpResponseNotFound('default')
        api.keystone.domain_delete(request, id)

    @rest_utils.ajax(data_required=True)
    def patch(self, request, id):
        """Update a single domain.

        The PATCH data should be an application/json object with the attributes
        to set to new values: "name" (string), "description" (string) and
        "enabled" (boolean).

        This method returns HTTP 204 (no content) on success.
        """
        api.keystone.domain_update(
            request,
            id,
            description=request.DATA.get('description'),
            enabled=request.DATA.get('enabled'),
            name=request.DATA.get('name')
        )


def _tenant_kwargs_from_DATA(data, enabled=True):
    # tenant_create takes arbitrary keyword arguments with only a small
    # restriction (the default args)
    kwargs = {'name': None, 'description': None, 'enabled': enabled,
              'domain': data.pop('domain_id', None)}
    kwargs.update(data)
    return kwargs


@urls.register
class Projects(generic.View):
    """API over all projects.

    Note that in the following "project" is used exclusively where in the
    underlying keystone API the terms "project" and "tenant" are used
    interchangeably.
    """
    url_regex = r'keystone/projects/$'
    client_keywords = {'paginate', 'marker', 'domain_id',
                       'user_id', 'admin'}

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of projects.

        By default a listing of all projects for the current domain are
        returned.

        You may specify GET parameters for domain_id (string), user_id
        (string) and admin (boolean) to change that listing's context.
        Additionally, paginate (boolean) and marker may be used to get
        paginated listings.

        The listing result is an object with properties:

        items
            The list of project objects.
        has_more
            Boolean indicating there are more results when pagination is used.
        """

        filters = rest_utils.parse_filters_kwargs(request,
                                                  self.client_keywords)[0]
        if len(filters) == 0:
            filters = None

        paginate = request.GET.get('paginate') == 'true'
        admin = False if request.GET.get('admin') == 'false' else True

        result, has_more = api.keystone.tenant_list(
            request,
            paginate=paginate,
            marker=request.GET.get('marker'),
            domain=request.GET.get('domain_id'),
            user=request.GET.get('user_id'),
            admin=admin,
            filters=filters
        )
        # return (list of results, has_more_data)
        return dict(has_more=has_more, items=[d.to_dict() for d in result])

    @rest_utils.ajax(data_required=True)
    def post(self, request):
        """Create a project (tenant).

        Create a project using parameters supplied in the POST
        application/json object. The "name" (string) parameter is required,
        others are optional: "description" (string), "domain_id" (string) and
        "enabled" (boolean, defaults to true). Additional, undefined
        parameters may also be provided, but you'll have to look deep into
        keystone to figure out what they might be.

        This method returns the new project object on success.
        """
        kwargs = _tenant_kwargs_from_DATA(request.DATA)
        if not kwargs['name']:
            raise rest_utils.AjaxError(400, '"name" is required')
        new_project = api.keystone.tenant_create(
            request,
            kwargs.pop('name'),
            **kwargs
        )
        return rest_utils.CreatedResponse(
            '/api/keystone/projects/%s' % new_project.id,
            new_project.to_dict()
        )

    @rest_utils.ajax(data_required=True)
    def delete(self, request):
        """Delete multiple projects by id.

        The DELETE data should be an application/json array of project ids to
        delete.

        This method returns HTTP 204 (no content) on success.
        """
        for id in request.DATA:
            api.keystone.tenant_delete(request, id)


@urls.register
class Project(generic.View):
    """API over a single project.

    Note that in the following "project" is used exclusively where in the
    underlying keystone API the terms "project" and "tenant" are used
    interchangeably.
    """
    url_regex = r'keystone/projects/(?P<id>[0-9a-f]+)$'

    @rest_utils.ajax()
    def get(self, request, id):
        """Get a specific project by id.
        """
        return api.keystone.tenant_get(request, id).to_dict()

    @rest_utils.ajax()
    def delete(self, request, id):
        """Delete a single project by id.

        This method returns HTTP 204 (no content) on success.
        """
        api.keystone.tenant_delete(request, id)

    @rest_utils.ajax(data_required=True)
    def patch(self, request, id):
        """Update a single project.

        The PATCH data should be an application/json object with  the
        attributes to set to new values: "name" (string),  "description"
        (string), "domain_id" (string) and "enabled" (boolean). Additional,
        undefined parameters may also be provided, but you'll have to look
        deep into keystone to figure out what they might be.

        This method returns HTTP 204 (no content) on success.
        """
        kwargs = _tenant_kwargs_from_DATA(request.DATA, enabled=None)
        api.keystone.tenant_update(request, id, **kwargs)


@urls.register
class ProjectRole(generic.View):
    url_regex = r'keystone/projects/(?P<project_id>[0-9a-f]+)/' \
                '(?P<role_id>[0-9a-f]+)/(?P<user_id>[0-9a-f]+)$'

    @rest_utils.ajax()
    def put(self, request, project_id, role_id, user_id):
        """Grant the specified role to the user in the project (tenant).

        This method takes no data.

        This method returns HTTP 204 (no content) on success.
        """
        api.keystone.add_tenant_user_role(
            request,
            project_id,
            user_id,
            role_id
        )


@urls.register
class ServiceCatalog(generic.View):
    url_regex = r'keystone/svc-catalog/$'

    @rest_utils.ajax()
    def get(self, request):
        """Return the Keystone service catalog associated with the current
        user.
        """
        return request.user.service_catalog


@urls.register
class UserSession(generic.View):
    """API for a single keystone user.
    """
    url_regex = r'keystone/user-session/$'
    allowed_fields = {
        'available_services_regions',
        'domain_id',
        'domain_name',
        'enabled',
        'id',
        'is_superuser',
        'project_id',
        'project_name',
        'roles',
        'services_region',
        'user_domain_id',
        'user_domain_name',
        'username'
    }

    @rest_utils.ajax()
    def get(self, request):
        """Get the current user session.
        """
        return {k: getattr(request.user, k, None) for k in self.allowed_fields}
