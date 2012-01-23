# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 CRS4
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
General-purpose decorators for use with Horizon.
"""
import functools

from django.utils.decorators import available_attrs

from horizon.exceptions import NotAuthorized


def _current_component(view_func, dashboard=None, panel=None):
    """ Sets the currently-active dashboard and/or panel on the request. """
    @functools.wraps(view_func, assigned=available_attrs(view_func))
    def dec(request, *args, **kwargs):
        if dashboard:
            request.horizon['dashboard'] = dashboard
        if panel:
            request.horizon['panel'] = panel
        return view_func(request, *args, **kwargs)
    return dec


def require_roles(view_func, required):
    """ Enforces role-based access controls.

    :param list required: A tuple of role names, all of which the request user
                          must possess in order access the decorated view.

    Example usage::

        from horizon.decorators import require_roles


        @require_roles(['admin', 'member'])
        def my_view(request):
            ...

    Raises a :exc:`~horizon.exceptions.NotAuthorized` exception if the
    requirements are not met.
    """
    # We only need to check each role once for a view, so we'll use a set
    current_roles = getattr(view_func, '_required_roles', set([]))
    view_func._required_roles = current_roles | set(required)

    @functools.wraps(view_func, assigned=available_attrs(view_func))
    def dec(request, *args, **kwargs):
        if request.user.is_authenticated():
            roles = set([role['name'].lower() for role in request.user.roles])
            # set operator <= tests that all members of set 1 are in set 2
            if view_func._required_roles <= set(roles):
                return view_func(request, *args, **kwargs)
        raise NotAuthorized("You are not authorized to access %s"
                            % request.path)

    # If we don't have any roles, just return the original view.
    if required:
        return dec
    else:
        return view_func


def enforce_admin_access(view_func):
    """ Marks a view as requiring the ``"admin"`` role for access. """
    return require_roles(view_func, ('admin',))
