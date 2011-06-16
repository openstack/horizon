# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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
Better wrappers for errors from Nova's admin api.
"""

import boto.exception
from django.shortcuts import redirect
from django.core import exceptions as core_exceptions


class NovaServerError(Exception):
    """
    Consumes a BotoServerError and gives more meaningful errors.
    """
    def __init__(self, ec2error):
        self.status = ec2error.status
        self.message = ec2error.reason

    def __str__(self):
        return self.message


class NovaApiError(Exception):
    """
    Used when Nova returns a 400 Bad Request status.
    """
    def __init__(self, ec2error):
        self.message = ec2error.error_message

    def __str__(self):
        return self.message


class NovaUnavailableError(NovaServerError):
    """
    Used when Nova returns a 503 Service Unavailable status.
    """
    pass


class NovaUnauthorizedError(core_exceptions.PermissionDenied):
    """
    Used when Nova returns a 401 Not Authorized status.
    """
    pass


def wrap_nova_error(func):
    """
    Used to decorate a function that interacts with boto. It will catch
    and convert boto server errors and reraise as a more specific nova error.
    """
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except boto.exception.BotoServerError, e:
            if e.status == 400 and e.error_code == 'ApiError':
                raise NovaApiError(e)
            elif e.status == 401:
                raise NovaUnauthorizedError()
            elif e.status == 503:
                raise NovaUnavailableError(e)
            raise NovaServerError(e)
    return decorator


def handle_nova_error(func):
    """
    Decorator for handling nova errors in a generalized way.
    """
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except NovaUnavailableError:
            return redirect('nova_unavailable')
    return decorator
