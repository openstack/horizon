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

from collections import defaultdict
from collections import OrderedDict
import logging
import types
import warnings

from django.conf import settings
from django.core import urlresolvers
from django import shortcuts
from django.template.loader import render_to_string  # noqa
from django.utils.functional import Promise  # noqa
from django.utils.http import urlencode  # noqa
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy
import six

from horizon import messages
from horizon.utils import functions
from horizon.utils import html


LOG = logging.getLogger(__name__)

# For Bootstrap integration; can be overridden in settings.
ACTION_CSS_CLASSES = ()
STRING_SEPARATOR = "__"


class BaseActionMetaClass(type):
    """Metaclass for adding all actions options from inheritance tree
    to action.
    This way actions can inherit from each other but still use
    the class attributes DSL. Meaning, all attributes of Actions are
    defined as class attributes, but in the background, it will be used as
    parameters for the initializer of the object. The object is then
    initialized clean way. Similar principle is used in DataTableMetaclass.
    """
    def __new__(mcs, name, bases, attrs):
        # Options of action are set as class attributes, loading them.
        options = {}
        if attrs:
            options = attrs

        # Iterate in reverse to preserve final order
        for base in bases[::-1]:
            # It actually throws all super classes away except immediate
            # superclass. But it's fine, immediate super-class base_options
            # includes everything because superclasses was created also by
            # this metaclass. Same principle is used in DataTableMetaclass.
            if hasattr(base, 'base_options') and base.base_options:
                base_options = {}
                # Updating options by superclasses.
                base_options.update(base.base_options)
                # Updating superclass options by actual class options.
                base_options.update(options)
                options = base_options
        # Saving all options to class attribute, this will be used for
        # instantiating of the specific Action.
        attrs['base_options'] = options

        return type.__new__(mcs, name, bases, attrs)

    def __call__(cls, *args, **kwargs):
        cls.base_options.update(kwargs)
        # Adding cls.base_options to each init call.
        klass = super(BaseActionMetaClass, cls).__call__(
            *args, **cls.base_options)
        return klass


@six.add_metaclass(BaseActionMetaClass)
class BaseAction(html.HTMLElement):
    """Common base class for all ``Action`` classes."""

    def __init__(self, **kwargs):
        super(BaseAction, self).__init__()
        self.datum = kwargs.get('datum', None)
        self.table = kwargs.get('table', None)
        self.handles_multiple = kwargs.get('handles_multiple', False)
        self.requires_input = kwargs.get('requires_input', False)
        self.preempt = kwargs.get('preempt', False)
        self.policy_rules = kwargs.get('policy_rules', None)

    def data_type_matched(self, datum):
        """Method to see if the action is allowed for a certain type of data.
        Only affects mixed data type tables.
        """
        if datum:
            action_data_types = getattr(self, "allowed_data_types", [])
            # If the data types of this action is empty, we assume it accepts
            # all kinds of data and this method will return True.
            if action_data_types:
                datum_type = getattr(datum, self.table._meta.data_type_name,
                                     None)
                if datum_type and (datum_type not in action_data_types):
                    return False
        return True

    def get_policy_target(self, request, datum):
        """Provide the target for a policy request.

        This method is meant to be overridden to return target details when
        one of the policy checks requires them.  E.g., {"user_id": datum.id}
        """
        return {}

    def allowed(self, request, datum):
        """Determine whether this action is allowed for the current request.

        This method is meant to be overridden with more specific checks.
        """
        return True

    def _allowed(self, request, datum):
        policy_check = getattr(settings, "POLICY_CHECK_FUNCTION", None)

        if policy_check and self.policy_rules:
            target = self.get_policy_target(request, datum)
            return (policy_check(self.policy_rules, request, target) and
                    self.allowed(request, datum))
        return self.allowed(request, datum)

    def update(self, request, datum):
        """Allows per-action customization based on current conditions.

        This is particularly useful when you wish to create a "toggle"
        action that will be rendered differently based on the value of an
        attribute on the current row's data.

        By default this method is a no-op.
        """
        pass

    def get_default_classes(self):
        """Returns a list of the default classes for the action. Defaults to
        ``["btn", "btn-default", "btn-sm"]``.
        """
        return getattr(settings, "ACTION_CSS_CLASSES", ACTION_CSS_CLASSES)

    def get_default_attrs(self):
        """Returns a list of the default HTML attributes for the action.
        Defaults to returning an ``id`` attribute with the value
        ``{{ table.name }}__action_{{ action.name }}__{{ creation counter }}``.
        """
        if self.datum is not None:
            bits = (self.table.name,
                    "row_%s" % self.table.get_object_id(self.datum),
                    "action_%s" % self.name)
        else:
            bits = (self.table.name, "action_%s" % self.name)
        return {"id": STRING_SEPARATOR.join(bits)}

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.name)

    def associate_with_table(self, table):
        self.table = table


class Action(BaseAction):
    """Represents an action which can be taken on this table's data.

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

    .. attribute:: preempt

        Boolean value indicating whether this action should be evaluated in
        the period after the table is instantiated but before the data has
        been loaded.

        This can allow actions which don't need access to the full table data
        to bypass any API calls and processing which would otherwise be
        required to load the table.

    .. attribute:: allowed_data_types

        A list that contains the allowed data types of the action.  If the
        datum's type is in this list, the action will be shown on the row
        for the datum.

        Default to be an empty list (``[]``). When set to empty, the action
        will accept any kind of data.

    .. attribute:: policy_rules

        list of scope and rule tuples to do policy checks on, the
        composition of which is (scope, rule)

            scope: service type managing the policy for action
            rule: string representing the action to be checked

            for a policy that requires a single rule check:
                policy_rules should look like
                    "(("compute", "compute:create_instance"),)"
            for a policy that requires multiple rule checks:
                rules should look like
                    "(("identity", "identity:list_users"),
                      ("identity", "identity:list_roles"))"

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

    def __init__(self, single_func=None, multiple_func=None, handle_func=None,
                 attrs=None, **kwargs):
        super(Action, self).__init__(**kwargs)

        self.method = kwargs.get('method', "POST")
        self.requires_input = kwargs.get('requires_input', True)
        self.verbose_name = kwargs.get('verbose_name', self.name.title())
        self.verbose_name_plural = kwargs.get('verbose_name_plural',
                                              "%ss" % self.verbose_name)
        self.allowed_data_types = kwargs.get('allowed_data_types', [])
        self.icon = kwargs.get('icon', None)

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
            self.single = types.MethodType(single, self)

        if not has_multiple and self.handles_multiple:
            def multiple(self, data_table, request, object_ids):
                return self.handle(data_table, request, object_ids)
            self.multiple = types.MethodType(multiple, self)

    def get_param_name(self):
        """Returns the full POST parameter name for this action.

        Defaults to
        ``{{ table.name }}__{{ action.name }}``.
        """
        return "__".join([self.table.name, self.name])


class LinkAction(BaseAction):
    """A table action which is simply a link rather than a form POST.

    .. attribute:: name

        Required. The short name or "slug" representing this
        action. This name should not be changed at runtime.

    .. attribute:: verbose_name

        A string which will be rendered as the link text. (Required)

    .. attribute:: url

        A string or a callable which resolves to a url to be used as the link
        target. You must either define the ``url`` attribute or override
        the ``get_link_url`` method on the class.

    .. attribute:: allowed_data_types

        A list that contains the allowed data types of the action.  If the
        datum's type is in this list, the action will be shown on the row
        for the datum.

        Defaults to be an empty list (``[]``). When set to empty, the action
        will accept any kind of data.
    """
    # class attribute name is used for ordering of Actions in table
    name = "link"
    ajax = False

    def __init__(self, attrs=None, **kwargs):
        super(LinkAction, self).__init__(**kwargs)
        self.method = kwargs.get('method', "GET")
        self.bound_url = kwargs.get('bound_url', None)
        self.name = kwargs.get('name', self.name)
        self.verbose_name = kwargs.get('verbose_name', self.name.title())
        self.url = kwargs.get('url', None)
        self.allowed_data_types = kwargs.get('allowed_data_types', [])
        self.icon = kwargs.get('icon', None)
        self.kwargs = kwargs

        if not kwargs.get('verbose_name', None):
            raise NotImplementedError('A LinkAction object must have a '
                                      'verbose_name attribute.')
        if attrs:
            self.attrs.update(attrs)
        if self.ajax:
            self.classes = list(self.classes) + ['ajax-update']

    def get_ajax_update_url(self):
        table_url = self.table.get_absolute_url()
        params = urlencode(
            OrderedDict([("action", self.name), ("table", self.table.name)])
        )
        return "%s?%s" % (table_url, params)

    def render(self):
        return render_to_string("horizon/common/_data_table_action.html",
                                {"action": self, "is_single": True})

    def associate_with_table(self, table):
        super(LinkAction, self).associate_with_table(table)
        if self.ajax:
            self.attrs['data-update-url'] = self.get_ajax_update_url()

    def get_link_url(self, datum=None):
        """Returns the final URL based on the value of ``url``.

        If ``url`` is callable it will call the function.
        If not, it will then try to call ``reverse`` on ``url``.
        Failing that, it will simply return the value of ``url`` as-is.

        When called for a row action, the current row data object will be
        passed as the first parameter.
        """
        if not self.url:
            raise NotImplementedError('A LinkAction class must have a '
                                      'url attribute or define its own '
                                      'get_link_url method.')
        if callable(self.url):
            return self.url(datum, **self.kwargs)
        try:
            if datum:
                obj_id = self.table.get_object_id(datum)
                return urlresolvers.reverse(self.url, args=(obj_id,))
            else:
                return urlresolvers.reverse(self.url)
        except urlresolvers.NoReverseMatch as ex:
            LOG.info('No reverse found for "%s": %s' % (self.url, ex))
            return self.url


class FilterAction(BaseAction):
    """A base class representing a filter action for a table.

    .. attribute:: name

        The short name or "slug" representing this action. Defaults to
        ``"filter"``.

    .. attribute:: verbose_name

        A descriptive name used for display purposes. Defaults to the
        value of ``name`` with the first letter of each word capitalized.

    .. attribute:: param_name

        A string representing the name of the request parameter used for the
        search term. Default: ``"q"``.

    .. attribute:: filter_type

        A string representing the type of this filter. If this is set to
        ``"server"`` then ``filter_choices`` must also be provided.
        Default: ``"query"``.

    .. attribute:: filter_choices

        Required for server type filters. A tuple of tuples representing the
        filter options. Tuple composition should evaluate to (string, string,
        boolean), representing the filter parameter, display value, and whether
        or not it should be applied to the API request as an API query
        attribute. API type filters do not need to be accounted for in the
        filter method since the API will do the filtering. However, server
        type filters in general will need to be performed in the filter method.
        By default this attribute is not provided.

    .. attribute:: needs_preloading

        If True, the filter function will be called for the initial
        GET request with an empty ``filter_string``, regardless of the
        value of ``method``.
    """
    # TODO(gabriel): The method for a filter action should be a GET,
    # but given the form structure of the table that's currently impossible.
    # At some future date this needs to be reworked to get the filter action
    # separated from the table's POST form.

    # class attribute name is used for ordering of Actions in table
    name = "filter"

    def __init__(self, **kwargs):
        super(FilterAction, self).__init__(**kwargs)
        self.method = kwargs.get('method', "POST")
        self.name = kwargs.get('name', self.name)
        self.verbose_name = kwargs.get('verbose_name', _("Filter"))
        self.filter_type = kwargs.get('filter_type', "query")
        self.filter_choices = kwargs.get('filter_choices')
        self.needs_preloading = kwargs.get('needs_preloading', False)
        self.param_name = kwargs.get('param_name', 'q')
        self.icon = "search"

        if self.filter_type == 'server' and self.filter_choices is None:
            raise NotImplementedError(
                'A FilterAction object with the '
                'filter_type attribute set to "server" must also have a '
                'filter_choices attribute.')

    def get_param_name(self):
        """Returns the full query parameter name for this action.

        Defaults to
        ``{{ table.name }}__{{ action.name }}__{{ action.param_name }}``.
        """
        return "__".join([self.table.name, self.name, self.param_name])

    def assign_type_string(self, table, data, type_string):
        for datum in data:
            setattr(datum, table._meta.data_type_name, type_string)

    def data_type_filter(self, table, data, filter_string):
        filtered_data = []
        for data_type in table._meta.data_types:
            func_name = "filter_%s_data" % data_type
            filter_func = getattr(self, func_name, None)
            if not filter_func and not callable(filter_func):
                # The check of filter function implementation should happen
                # in the __init__. However, the current workflow of DataTable
                # and actions won't allow it. Need to be fixed in the future.
                cls_name = self.__class__.__name__
                raise NotImplementedError("You must define a %s method "
                                          "for %s data type in %s." %
                                          (func_name, data_type, cls_name))
            _data = filter_func(table, data, filter_string)
            self.assign_type_string(table, _data, data_type)
            filtered_data.extend(_data)
        return filtered_data

    def filter(self, table, data, filter_string):
        """Provides the actual filtering logic.

        This method must be overridden by subclasses and return
        the filtered data.
        """
        return data

    def is_api_filter(self, filter_field):
        """Determine if the given filter field should be used as an
        API filter.
        """
        if self.filter_type == 'server':
            for choice in self.filter_choices:
                if (choice[0] == filter_field and len(choice) > 2 and
                        choice[2] is True):
                    return True
        return False


class NameFilterAction(FilterAction):
    """A filter action for name property."""

    def filter(self, table, items, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [item for item in items
                if query in item.name.lower()]


class FixedFilterAction(FilterAction):
    """A filter action with fixed buttons."""

    def __init__(self, **kwargs):
        super(FixedFilterAction, self).__init__(**kwargs)
        self.filter_type = kwargs.get('filter_type', "fixed")
        self.needs_preloading = kwargs.get('needs_preloading', True)

        self.fixed_buttons = self.get_fixed_buttons()
        self.filter_string = ''

    def filter(self, table, images, filter_string):
        self.filter_string = filter_string
        categories = self.categorize(table, images)
        self.categories = defaultdict(list, categories)
        for button in self.fixed_buttons:
            button['count'] = len(self.categories[button['value']])
        if not filter_string:
            return images
        return self.categories[filter_string]

    def get_fixed_buttons(self):
        """Returns a list of dictionaries describing the fixed buttons
        to use for filtering.

        Each list item should be a dict with the following keys:

        * ``text``: Text to display on the button
        * ``icon``: Icon class for icon element (inserted before text).
        * ``value``: Value returned when the button is clicked. This value is
          passed to ``filter()`` as ``filter_string``.
        """
        return []

    def categorize(self, table, images):
        """Override to separate images into categories.

        Return a dict with a key for the value of each fixed button,
        and a value that is a list of images in that category.
        """
        return {}


class BatchAction(Action):
    """A table action which takes batch action on one or more
    objects. This action should not require user input on a
    per-object basis.

    .. attribute:: name

       An internal name for this action.

    .. method:: action_present

       Method accepting an integer/long parameter and returning the display
       forms of the name properly pluralised (depending on the integer) and
       translated in a string or tuple/list.

    .. attribute:: action_present (Deprecated)

       String or tuple/list. The display forms of the name.
       Should be a transitive verb, capitalized and translated. ("Delete",
       "Rotate", etc.) If tuple or list - then setting
       self.current_present_action = n will set the current active item
       from the list(action_present[n])

       You can pass a complete action name including 'data_type' by specifying
       '%(data_type)s' substitution in action_present ("Delete %(data_type)s").
       Otherwise a complete action name is a format of "<action> <data_type>".
       <data_type> is determined based on the number of items.
       By passing a complete action name you allow translators to control
       the order of words as they want.

       NOTE: action_present attribute is bad for translations and should be
       avoided. Please use the action_present method instead.
       This form is kept for legacy.

    .. method:: action_past

       Method accepting an integer/long parameter and returning the display
       forms of the name properly pluralised (depending on the integer) and
       translated in a string or tuple/list.

    .. attribute:: action_past (Deprecated)

       String or tuple/list. The past tense of action_present. ("Deleted",
       "Rotated", etc.) If tuple or list - then
       setting self.current_past_action = n will set the current active item
       from the list(action_past[n])

       NOTE: action_past attribute is bad for translations and should be
       avoided. Please use the action_past method instead.
       This form is kept for legacy.

    .. attribute:: data_type_singular (Deprecated)

       Optional display name (if the data_type method is not defined) for the
       type of data that receives the action. ("Key Pair", "Floating IP", etc.)

    .. attribute:: data_type_plural (Deprecated)

       Optional plural word (if the data_type method is not defined) for the
       type of data being acted on. Defaults to appending 's'. Relying on the
       default is bad for translations and should not be done, so it's absence
       will raise a DeprecationWarning. It is currently kept as optional for
       legacy code.

       NOTE: data_type_singular and data_type_plural attributes are bad for
       translations and should not be used. Please use the action_present and
       action_past methods. This form is kept temporarily for legacy code but
       will be removed.

    .. attribute:: success_url

       Optional location to redirect after completion of the delete
       action. Defaults to the current page.

    .. attribute:: help_text

       Optional message for providing an appropriate help text for
       the horizon user.
    """

    help_text = _("This action cannot be undone.")

    def __init__(self, **kwargs):
        super(BatchAction, self).__init__(**kwargs)

        action_present_method = False
        if hasattr(self, 'action_present'):
            if callable(self.action_present):
                action_present_method = True
            else:
                warnings.warn(DeprecationWarning(
                    'The %s BatchAction class must have an action_present '
                    'method instead of attribute.' % self.__class__.__name__
                ))

        action_past_method = False
        if hasattr(self, 'action_past'):
            if callable(self.action_past):
                action_past_method = True
            else:
                warnings.warn(DeprecationWarning(
                    'The %s BatchAction class must have an action_past '
                    'method instead of attribute.' % self.__class__.__name__
                ))

        action_methods = action_present_method and action_past_method
        has_action_method = action_present_method or action_past_method

        if has_action_method and not action_methods:
            raise NotImplementedError(
                'The %s BatchAction class must have both action_past and'
                'action_present methods.' % self.__class__.__name__
            )

        if not action_methods:
            if not kwargs.get('data_type_singular'):
                raise NotImplementedError(
                    'The %s BatchAction class must have a data_type_singular '
                    'attribute when action_past and action_present attributes '
                    'are used.' % self.__class__.__name__
                )
            self.data_type_singular = kwargs.get('data_type_singular')
            self.data_type_plural = kwargs.get('data_type_plural',
                                               self.data_type_singular + 's')

        # TODO(ygbo): get rid of self.use_action_method once action_present and
        # action_past are changed to methods handling plurals.
        self.use_action_method = action_methods

        self.success_url = kwargs.get('success_url', None)
        # If setting a default name, don't initialize it too early
        self.verbose_name = kwargs.get('verbose_name', self._get_action_name)
        self.verbose_name_plural = kwargs.get(
            'verbose_name_plural',
            lambda: self._get_action_name('plural'))

        self.current_present_action = 0
        self.current_past_action = 0
        # Keep record of successfully handled objects
        self.success_ids = []

        self.help_text = kwargs.get('help_text', self.help_text)

    def _allowed(self, request, datum=None):
        # Override the default internal action method to prevent batch
        # actions from appearing on tables with no data.
        if not self.table.data and not datum:
            return False
        return super(BatchAction, self)._allowed(request, datum)

    def _get_action_name(self, items=None, past=False):
        """Builds combinations like 'Delete Object' and 'Deleted
        Objects' based on the number of items and `past` flag.

        :param items:

            A list or tuple of items (or container with a __len__ method) to
            count the number of concerned items for which this method is
            called.
            When this method is called for a single item (by the BatchAction
            itself), this parameter can be omitted and the number of items
            will be considered as "one".
            If we want to evaluate to "zero" this parameter must not be omitted
            (and should be an empty container).

        :param past:

            Boolean flag indicating if the action took place in the past.
            By default a present action is considered.
        """
        action_type = "past" if past else "present"
        if items is None:
            # Called without items parameter (by a single instance.)
            count = 1
        else:
            count = len(items)

        # TODO(ygbo): get rid of self.use_action_method once action_present and
        # action_past are changed to methods handling plurals.
        action_attr = getattr(self, "action_%s" % action_type)
        if self.use_action_method:
            action_attr = action_attr(count)
        if isinstance(action_attr, (six.string_types, Promise)):
            action = action_attr
        else:
            toggle_selection = getattr(self, "current_%s_action" % action_type)
            action = action_attr[toggle_selection]

        if self.use_action_method:
            return action
        # TODO(ygbo): get rid of all this bellow once action_present and
        # action_past are changed to methods handling plurals.
        data_type = ungettext_lazy(
            self.data_type_singular,
            self.data_type_plural,
            count
        )
        if '%(data_type)s' in action:
            # If full action string is specified, use action as format string.
            msgstr = action
        else:
            if action_type == "past":
                msgstr = pgettext_lazy(u"past", "%(action)s %(data_type)s")
            else:
                msgstr = pgettext_lazy(u"present", "%(action)s %(data_type)s")
        return msgstr % {'action': action, 'data_type': data_type}

    def action(self, request, datum_id):
        """Required. Accepts a single object id and performs the specific
        action.

        Return values are discarded, errors raised are caught and logged.
        """

    def update(self, request, datum):
        """Switches the action verbose name, if needed."""
        if getattr(self, 'action_present', False):
            self.verbose_name = self._get_action_name()
            self.verbose_name_plural = self._get_action_name('plural')

    def get_success_url(self, request=None):
        """Returns the URL to redirect to after a successful action."""
        if self.success_url:
            return self.success_url
        return request.get_full_path()

    def get_default_attrs(self):
        """Returns a list of the default HTML attributes for the action."""
        attrs = super(BatchAction, self).get_default_attrs()
        attrs.update({'data-batch-action': 'true'})
        return attrs

    def handle(self, table, request, obj_ids):
        action_success = []
        action_failure = []
        action_not_allowed = []
        for datum_id in obj_ids:
            datum = table.get_object_by_id(datum_id)
            datum_display = table.get_object_display(datum) or datum_id
            if not table._filter_action(self, request, datum):
                action_not_allowed.append(datum_display)
                LOG.warning(u'Permission denied to %s: "%s"' %
                            (self._get_action_name(past=True).lower(),
                             datum_display))
                continue
            try:
                self.action(request, datum_id)
                # Call update to invoke changes if needed
                self.update(request, datum)
                action_success.append(datum_display)
                self.success_ids.append(datum_id)
                LOG.info(u'%s: "%s"' %
                         (self._get_action_name(past=True), datum_display))
            except Exception as ex:
                # Handle the exception but silence it since we'll display
                # an aggregate error message later. Otherwise we'd get
                # multiple error messages displayed to the user.
                action_failure.append(datum_display)
                action_description = (
                    self._get_action_name(past=True).lower(), datum_display)
                LOG.warning(
                    'Action %(action)s Failed for %(reason)s', {
                        'action': action_description, 'reason': ex})

        # Begin with success message class, downgrade to info if problems.
        success_message_level = messages.success
        if action_not_allowed:
            msg = _('You are not allowed to %(action)s: %(objs)s')
            params = {"action":
                      self._get_action_name(action_not_allowed).lower(),
                      "objs": functions.lazy_join(", ", action_not_allowed)}
            messages.error(request, msg % params)
            success_message_level = messages.info
        if action_failure:
            msg = _('Unable to %(action)s: %(objs)s')
            params = {"action": self._get_action_name(action_failure).lower(),
                      "objs": functions.lazy_join(", ", action_failure)}
            messages.error(request, msg % params)
            success_message_level = messages.info
        if action_success:
            msg = _('%(action)s: %(objs)s')
            params = {"action":
                      self._get_action_name(action_success, past=True),
                      "objs": functions.lazy_join(", ", action_success)}
            success_message_level(request, msg % params)

        return shortcuts.redirect(self.get_success_url(request))


class DeleteAction(BatchAction):
    """A table action used to perform delete operations on table data.

    .. attribute:: name

        A short name or "slug" representing this action.
        Defaults to 'delete'

    .. method:: action_present

        Method accepting an integer/long parameter and returning the display
        forms of the name properly pluralised (depending on the integer) and
        translated in a string or tuple/list.

    .. attribute:: action_present (Deprecated)

        A string containing the transitive verb describing the delete action.
        Defaults to 'Delete'

        NOTE: action_present attribute is bad for translations and should be
        avoided. Please use the action_present method instead.
        This form is kept for legacy.

    .. method:: action_past

        Method accepting an integer/long parameter and returning the display
        forms of the name properly pluralised (depending on the integer) and
        translated in a string or tuple/list.

    .. attribute:: action_past (Deprecated)

        A string set to the past tense of action_present.
        Defaults to 'Deleted'

        NOTE: action_past attribute is bad for translations and should be
        avoided. Please use the action_past method instead.
        This form is kept for legacy.

    .. attribute:: data_type_singular (Deprecated)

        A string used to name the data to be deleted.

    .. attribute:: data_type_plural (Deprecated)

        Optional. Plural of ``data_type_singular``.
        Defaults to ``data_type_singular`` appended with an 's'.  Relying on
        the default is bad for translations and should not be done, so it's
        absence will raise a DeprecationWarning. It is currently kept as
        optional for legacy code.

        NOTE: data_type_singular and data_type_plural attributes are bad for
        translations and should not be used. Please use the action_present and
        action_past methods. This form is kept temporarily for legacy code but
        will be removed.
    """

    name = "delete"

    def __init__(self, **kwargs):
        super(DeleteAction, self).__init__(**kwargs)
        self.name = kwargs.get('name', self.name)
        if not hasattr(self, "action_present"):
            self.action_present = kwargs.get('action_present', _("Delete"))
        if not hasattr(self, "action_past"):
            self.action_past = kwargs.get('action_past', _("Deleted"))
        self.icon = "trash"

    def action(self, request, obj_id):
        """Action entry point. Overrides base class' action method.

        Accepts a single object id passing it over to the delete method
        responsible for the object's destruction.
        """
        return self.delete(request, obj_id)

    def delete(self, request, obj_id):
        """Required. Deletes an object referenced by obj_id.

        Override to provide delete functionality specific to your data.
        """

    def get_default_classes(self):
        """Appends ``btn-danger`` to the action's default css classes.

        This method ensures the corresponding button is highlighted
        as a trigger for a potentially dangerous action.
        """
        classes = super(DeleteAction, self).get_default_classes()
        classes += ("btn-danger",)
        return classes


class UpdateAction(object):
    """A table action for cell updates by inline editing."""
    name = "update"

    def action(self, request, datum, obj_id, cell_name, new_cell_value):
        self.update_cell(request, datum, obj_id, cell_name, new_cell_value)

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Update Item",
            u"Update Items",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Updated Item",
            u"Updated Items",
            count
        )

    def update_cell(self, request, datum, obj_id, cell_name, new_cell_value):
        """Method for saving data of the cell.

        This method must implements saving logic of the inline edited table
        cell.
        """

    def allowed(self, request, datum, cell):
        """Determine whether updating is allowed for the current request.

        This method is meant to be overridden with more specific checks.
        Data of the row and of the cell are passed to the method.
        """
        return True
