# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 Nebula, Inc.
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

import logging
import new

from django.forms.util import flatatt
from django.core import urlresolvers


LOG = logging.getLogger(__name__)


class BaseAction(object):
    """ Common base class for all ``Action`` classes. """
    table = None
    handles_multiple = False
    attrs = {}
    name = None

    def allowed(self, request, datum):
        """ Determine whether this action is allowed for the current request.

        This method is meant to be overridden with more specific checks.
        """
        return True

    def update(self, request, datum):
        """ Allows per-action customization based on current conditions.

        This is particularly useful when you wish to create a "toggle"
        action that will be rendered differently based on the value of an
        attribute on the current row's data.

        By default this method is a no-op.
        """
        pass

    @property
    def attr_string(self):
        """
        Returns a flattened string of HTML attributes based on the
        ``attrs`` dict provided to the class.
        """
        return flatatt(self.attrs)

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.name)


class Action(BaseAction):
    """ Represents an action which can be taken on this table's data.

    .. attribute:: name

        The short name or "slug" representing this action. Defaults to the
        name of the ``Action`` class.

    .. attribute:: verbose_name

        A descriptive name used for display purposes. Defaults to the
        value of ``name`` with the first letter of each word capitalized.

    .. attribute:: verbose_name_plural

        Used like ``verbose_name`` in cases where ``handles_multiple`` is
        ``True``. Defaults to ``verbose_name`` with the letter "s" appended.

    .. attribute:: method

        The HTTP method for this action. Defaults to ``POST``. Other methods
        may or may not succeed currently.

    At least one of the following methods must be defined:

    .. method:: single(self, data_table, request, object_id)

        Handler for a single-object action.

    .. method:: multiple(self, data_table, request, object_ids)

        Handler for multi-object actions.


    .. method:: handle(self, data_table, request, object_ids)

        If a single function can work for both single-object and
        multi-object cases then simply providing a ``handle`` function
        will internally route both ``single`` and ``multiple`` requests
        to ``handle`` with the calls from ``single`` being transformed
        into a list containing only the single object id.
    """
    method = "POST"

    def __init__(self, verbose_name=None, verbose_name_plural=None,
                 single_func=None, multiple_func=None, handle_func=None,
                 handles_multiple=False, attrs=None):
        super(Action, self).__init__()
        self.name = unicode(getattr(self, 'name', self.__class__.__name__))
        verbose_name = verbose_name or self.name.title()
        self.verbose_name = unicode(getattr(self,
                                            "verbose_name",
                                            verbose_name))
        verbose_name_plural = verbose_name_plural or "%ss" % self.verbose_name
        self.verbose_name_plural = unicode(getattr(self,
                                                   "verbose_name_plural",
                                                   verbose_name_plural))
        self.handles_multiple = getattr(self,
                                        "handles_multiple",
                                        handles_multiple)
        if attrs:
            self.attrs.update(attrs)

        # Don't set these if they're None
        if single_func:
            self.single = single_func
        if multiple_func:
            self.multiple = multiple_func
        if handle_func:
            self.handle = handle_func

        # Ensure we have the appropriate methods
        has_handler = hasattr(self, 'handle') and callable(self.handle)
        has_single = hasattr(self, 'single') and callable(self.single)
        has_multiple = hasattr(self, 'multiple') and callable(self.multiple)

        if has_handler or has_multiple:
            self.handles_multiple = True

        if not has_handler and (not has_single or has_multiple):
            raise ValueError('You must define either a "handle" method '
                             ' or a "single" or "multiple" method.')
        if not has_single:
            def single(self, data_table, request, object_id):
                return self.handle(data_table, request, [object_id])
            self.single = new.instancemethod(single, self)

        if not has_multiple and self.handles_multiple:
            def multiple(self, data_table, request, object_ids):
                return self.handle(data_table, request, object_ids)
            self.multiple = new.instancemethod(multiple, self)

    def get_param_name(self):
        """ Returns the full POST parameter name for this action.

        Defaults to
        ``{{ table.name }}__{{ action.name }}``.
        """
        return "__".join([self.table.name, self.name])


class LinkAction(BaseAction):
    """ A table action which is simply a link rather than a form POST.

    .. attribute:: verbose_name

        A string which will be rendered as the link text. (Required)

    .. attribute:: url

        A string or a callable which resolves to a url to be used as the link
        target. (Required)
    """
    method = "GET"
    bound_url = None

    def __init__(self, name=None, verbose_name=None, url=None, attrs=None):
        super(LinkAction, self).__init__()
        self.name = name or unicode(getattr(self,
                                            "name",
                                            self.__class__.__name__))
        verbose_name = verbose_name or self.name.title()
        self.verbose_name = unicode(getattr(self,
                                            "verbose_name",
                                            verbose_name))
        self.url = getattr(self, "url", url)
        if not self.verbose_name:
            raise ValueError('A LinkAction object must have a '
                             'verbose_name attribute.')
        if not self.url:
            raise ValueError('A LinkAction object must have a '
                             'url attribute.')
        if attrs:
            self.attrs.update(attrs)

    def get_link_url(self, datum=None, *args, **kwargs):
        """ Returns the final URL based on the value of ``url``.

        If ``url`` is callable it will call the function.
        If not, it will then try to call ``reverse`` on ``url``.
        Failing that, it will simply return the value of ``url`` as-is.

        When called for a row action, the current row data object will be
        passed as the first parameter.
        """
        if callable(self.url):
            return self.url(datum, *args, **kwargs)
        try:
            if datum:
                obj_id = self.table.get_object_id(datum)
                return urlresolvers.reverse(self.url, args=(obj_id,))
            else:
                return urlresolvers.reverse(self.url)
        except urlresolvers.NoReverseMatch, ex:
            LOG.info('No reverse found for "%s": %s' % (self.url, ex))
            return self.url


class FilterAction(BaseAction):
    """ A base class representing a filter action for a table.

    .. attribute:: name

        The short name or "slug" representing this action. Defaults to
        ``"filter"``.

    .. attribute:: verbose_name

        A descriptive name used for display purposes. Defaults to the
        value of ``name`` with the first letter of each word capitalized.

    .. attribute:: param_name

        A string representing the name of the request parameter used for the
        search term. Default: ``"q"``.
    """
    method = "GET"
    name = "filter"

    def __init__(self, name=None, verbose_name=None, param_name=None):
        super(FilterAction, self).__init__()
        self.name = name or self.name
        self.verbose_name = unicode(verbose_name) or self.name
        self.param_name = param_name or 'q'

    def get_param_name(self):
        """ Returns the full query parameter name for this action.

        Defaults to
        ``{{ table.name }}__{{ action.name }}__{{ action.param_name }}``.
        """
        return "__".join([self.table.name, self.name, self.param_name])

    def filter(self, table, data, filter_string):
        """ Provides the actual filtering logic.

        This method must be overridden by subclasses and return
        the filtered data.
        """
        raise NotImplementedError("The filter method has not been implemented "
                                  "by %s." % self.__class__)
