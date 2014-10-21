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

import six

from django.core.urlresolvers import reverse as django_reverse
from django.utils.http import urlquote  # noqa
from django import VERSION  # noqa


def reverse(viewname, urlconf=None, args=None, kwargs=None, prefix=None,
            current_app=None):
    if VERSION < (1, 6):
        if args:
            args = [urlquote(x) for x in args]
        if kwargs:
            kwargs = dict([(x, urlquote(y)) for x, y in six.iteritems(kwargs)])
    return django_reverse(viewname, urlconf, args, kwargs, prefix,
                          current_app)
