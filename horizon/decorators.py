# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 CRS4
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
from django.utils.translation import ugettext_lazy as _


def _current_component(view_func, dashboard=None, panel=None):
    """Sets the currently-active dashboard and/or panel on the request."""
    @functools.wraps(view_func, assigned=available_attrs(view_func))
    def dec(request, *args, **kwargs):
        if dashboard:
            request.horizon['dashboard'] = dashboard
        if panel:
            request.horizon['panel'] = panel
        return view_func(request, *args, **kwargs)
    return dec


def require_auth(view_func):
    """Performs user authentication check.

    Similar to Django's `login_required` decorator, except that this throws
    :exc:`~horizon.exceptions.NotAuthenticated` exception if the user is not
    signed-in.
    """
    from horizon.exceptions import NotAuthenticated

    @functools.wraps(view_func, assigned=available_attrs(view_func))
    def dec(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        raise NotAuthenticated(_("Please log in to continue."))
    return dec


def require_perms(view_func, required):
    """Enforces permission-based access controls.

    :param list required: A tuple of permission names, all of which the request
                          user must possess in order access the decorated view.

    Example usage::

        from horizon.decorators import require_perms


        @require_perms(['foo.admin', 'foo.member'])
        def my_view(request):
            ...

    Raises a :exc:`~horizon.exceptions.NotAuthorized` exception if the
    requirements are not met.
    """
    from horizon.exceptions import NotAuthorized
    # We only need to check each permission once for a view, so we'll use a set
    current_perms = getattr(view_func, '_required_perms', set([]))
    view_func._required_perms = current_perms | set(required)

    @functools.wraps(view_func, assigned=available_attrs(view_func))
    def dec(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.has_perms(view_func._required_perms):
                return view_func(request, *args, **kwargs)
        raise NotAuthorized(_("You are not authorized to access %s")
                            % request.path)

    # If we don't have any permissions, just return the original view.
    if required:
        return dec
    else:
        return view_func


def require_component_access(view_func, component):
    """Perform component can_access check to access the view.

    :param component containing the view (panel or dashboard).

    Raises a :exc:`~horizon.exceptions.NotAuthorized` exception if the
    user cannot access the component containing the view.
    By example the check of component policy rules will be applied to its
    views.
    """
    from horizon.exceptions import NotAuthorized

    @functools.wraps(view_func, assigned=available_attrs(view_func))
    def dec(request, *args, **kwargs):
        if not component.can_access({'request': request}):
            raise NotAuthorized(_("You are not authorized to access %s")
                                % request.path)

        return view_func(request, *args, **kwargs)

    return dec
