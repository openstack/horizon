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

import copy
import logging
import new

from django import shortcuts
from django.conf import settings
from django.forms.util import flatatt
from django.contrib import messages
from django.core import urlresolvers
from django.utils.translation import string_concat, ugettext as _

from horizon import exceptions


LOG = logging.getLogger(__name__)

# For Bootstrap integration, can be overridden in settings.
ACTION_CSS_CLASSES = ("btn", "small")


class BaseAction(object):
    """ Common base class for all ``Action`` classes. """
    table = None
    handles_multiple = False
    requires_input = False

    def __init__(self):
        self.attrs = getattr(self, "attrs", {})
        self.classes = getattr(self, "classes", [])

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
        final_attrs = copy.copy(self.attrs)
        # Handle css class concatenation
        default = " ".join(getattr(settings,
                                   "ACTION_CSS_CLASSES",
                                   ACTION_CSS_CLASSES))
        defined = self.attrs.get('class', '')
        additional = " ".join(self.classes)
        final_classes = " ".join((defined, default, additional)).strip()
        final_attrs.update({'class': final_classes})
        return flatatt(final_attrs)

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.name)


class Action(BaseAction):
    """ Represents an action which can be taken on this table's data.

    .. attribute:: name

        Required. The short name or "slug" representing this
        action. This name should not be changed at runtime.

    .. attribute:: verbose_name

        A descriptive name used for display purposes. Defaults to the
        value of ``name`` with the first letter of each word capitalized.

    .. attribute:: verbose_name_plural

        Used like ``verbose_name`` in cases where ``handles_multiple`` is
        ``True``. Defaults to ``verbose_name`` with the letter "s" appended.

    .. attribute:: method

        The HTTP method for this action. Defaults to ``POST``. Other methods
        may or may not succeed currently.

    .. attribute:: requires_input

        Boolean value indicating whether or not this action can be taken
        without any additional input (e.g. an object id). Defaults to ``True``.

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
    requires_input = True

    def __init__(self, verbose_name=None, verbose_name_plural=None,
                 single_func=None, multiple_func=None, handle_func=None,
                 handles_multiple=False, attrs=None, requires_input=True):
        super(Action, self).__init__()
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
        self.requires_input = getattr(self,
                                      "requires_input",
                                      requires_input)
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
            cls_name = self.__class__.__name__
            raise NotImplementedError('You must define either a "handle" '
                                      'method or a "single" or "multiple" '
                                      'method on %s.' % cls_name)

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

    .. attribute:: name

        Required. The short name or "slug" representing this
        action. This name should not be changed at runtime.

    .. attribute:: verbose_name

        A string which will be rendered as the link text. (Required)

    .. attribute:: url

        A string or a callable which resolves to a url to be used as the link
        target. (Required)
    """
    method = "GET"
    bound_url = None

    def __init__(self, verbose_name=None, url=None, attrs=None):
        super(LinkAction, self).__init__()
        verbose_name = verbose_name or self.name.title()
        self.verbose_name = unicode(getattr(self,
                                            "verbose_name",
                                            verbose_name))
        self.url = getattr(self, "url", url)
        if not self.verbose_name:
            raise NotImplementedError('A LinkAction object must have a '
                                      'verbose_name attribute.')
        if not self.url:
            raise NotImplementedError('A LinkAction object must have a '
                                      'url attribute.')
        if attrs:
            self.attrs.update(attrs)

    def get_link_url(self, datum=None):
        """ Returns the final URL based on the value of ``url``.

        If ``url`` is callable it will call the function.
        If not, it will then try to call ``reverse`` on ``url``.
        Failing that, it will simply return the value of ``url`` as-is.

        When called for a row action, the current row data object will be
        passed as the first parameter.
        """
        if callable(self.url):
            return self.url(datum, **self.kwargs)
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

    def __init__(self, verbose_name=None, param_name=None):
        super(FilterAction, self).__init__()
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


class BatchAction(Action):
    """ A table action which takes batch action on one or more
        objects. This action should not require user input on a
        per-object basis.

    .. attribute:: name

       An internal name for this action.

    .. attribute:: action_present

       The display form of the name. Should be a transitive verb,
       capitalized and translated. ("Delete", "Rotate", etc.)

    .. attribute:: action_past

       The past tense of action_present. ("Deleted", "Rotated", etc.)

    .. attribute:: data_type_singular

       A display name for the type of data that receives the
       action. ("Keypair", "Floating IP", etc.)

    .. attribute:: data_type_plural

       Optional plural word for the type of data being acted
       on. Defaults to appending 's'. Relying on the default is bad
       for translations and should not be done.

    .. attribute:: success_url

       Optional location to redirect after completion of the delete
       action. Defaults to the current page.
    """
    completion_url = None

    def _conjugate(self, items=None, past=False):
        """
        Builds combinations like 'Delete Object' and 'Deleted
        Objects' based on the number of items and `past` flag.
        """
        if past:
            action = self.action_past
        else:
            action = self.action_present
        if items is None or len(items) == 1:
            data_type = self.data_type_singular
        else:
            data_type = self.data_type_plural
        return string_concat(action, ' ', data_type)

    def __init__(self):
        self.data_type_plural = getattr(self, 'data_type_plural',
                                        self.data_type_singular + 's')
        self.verbose_name = getattr(self, 'verbose_name',
                                    self._conjugate())
        self.verbose_name_plural = getattr(self, 'verbose_name_plural',
                                           self._conjugate('plural'))
        super(BatchAction, self).__init__()

    def action(self, request, datum_id):
        """
        Required. Accepts a single object id and performs the specific action.

        Return values are discarded, errors raised are caught and logged.
        """
        raise NotImplementedError('action() must be defined for '
                                  'BatchAction: %s' % self.data_type_singular)

    def get_success_url(self, request=None):
        """
        Returns the URL to redirect to after a successful action.
        """
        if self.completion_url:
            return self.completion_url
        return request.get_full_path()

    def handle(self, table, request, obj_ids):
        action_success = []
        action_failure = []
        action_not_allowed = []
        for datum_id in obj_ids:
            datum = table.get_object_by_id(datum_id)
            datum_display = table.get_object_display(datum)
            if not table._filter_action(self, request, datum):
                action_not_allowed.append(datum_display)
                LOG.info('Permission denied to %s: "%s"' %
                         (self._conjugate(past=True).lower(), datum_display))
                continue
            try:
                self.action(request, datum_id)
                action_success.append(datum_display)
                LOG.info('%s: "%s"' %
                         (self._conjugate(past=True), datum_display))
            except:
                action_str = self._conjugate().lower()
                exceptions.handle(request,
                                  _("Unable to %s.") % action_str)
                action_failure.append(datum_display)

        #Begin with success message class, downgrade to info if problems
        success_message_level = messages.success
        if action_not_allowed:
            messages.error(request, _('You do not have permission to %s: %s') %
                           (self._conjugate(action_not_allowed).lower(),
                            ", ".join(action_not_allowed)))
            success_message_level = messages.info
        if action_failure:
            messages.error(request, _('Unable to %s: %s') % (
                    self._conjugate(action_failure).lower(),
                    ", ".join(action_failure)))
            success_message_level = messages.info
        if action_success:
            success_message_level(request, _('%s: %s') % (
                    self._conjugate(action_success, True),
                    ", ".join(action_success)))

        return shortcuts.redirect(self.get_success_url(request))


class DeleteAction(BatchAction):
    name = "delete"
    action_present = _("Delete")
    action_past = _("Deleted")
    classes = ('danger',)

    def action(self, request, obj_id):
        return self.delete(request, obj_id)

    def delete(self, request, obj_id):
        raise NotImplementedError("DeleteAction must define a delete method.")
