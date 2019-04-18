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
import copy
import inspect
import json
import logging
from operator import attrgetter
import sys

from django.conf import settings
from django.core import exceptions as core_exceptions
from django import forms
from django.http import HttpResponse
from django import template
from django.template.defaultfilters import slugify
from django.template.defaultfilters import truncatechars
from django.template.loader import render_to_string
from django import urls
from django.utils import encoding
from django.utils.html import escape
from django.utils import http
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils import termcolors
from django.utils.translation import ugettext_lazy as _
import six

from horizon import conf
from horizon import exceptions
from horizon.forms import ThemableCheckboxInput
from horizon import messages
from horizon.tables.actions import BatchAction
from horizon.tables.actions import FilterAction
from horizon.tables.actions import LinkAction
from horizon.utils import html
from horizon.utils import settings as utils_settings

# Python 3.8 removes the ability to import the abstract base classes from
# 'collections', but 'collections.abc' is not present in Python 2.7
# TODO(stephenfin): Remove when we drop support for Python 2.7
# pylint: disable=ungrouped-imports
if hasattr(collections, 'abc'):
    from collections.abc import Mapping
else:
    from collections import Mapping


LOG = logging.getLogger(__name__)
PALETTE = termcolors.PALETTES[termcolors.DEFAULT_PALETTE]
STRING_SEPARATOR = "__"


# 'getfullargspec' is Python 3-only, but 'getargspec' is deprecated for removal
# in Python 3.6
# TODO(stephenfin): Remove 'getargspec' when we drop support for Python 2.7
if hasattr(inspect, 'getfullargspec'):
    getargspec = inspect.getfullargspec
else:
    getargspec = inspect.getargspec


@six.python_2_unicode_compatible
class Column(html.HTMLElement):
    """A class which represents a single column in a :class:`.DataTable`.

    .. attribute:: transform

        A string or callable. If ``transform`` is a string, it should be the
        name of the attribute on the underlying data class which
        should be displayed in this column. If it is a callable, it
        will be passed the current row's data at render-time and should
        return the contents of the cell. Required.

    .. attribute:: verbose_name

        The name for this column which should be used for display purposes.
        Defaults to the value of ``transform`` with the first letter
        of each word capitalized if the ``transform`` is not callable,
        otherwise it defaults to an empty string (``""``).

    .. attribute:: sortable

        Boolean to determine whether this column should be sortable or not.
        Defaults to ``True``.

    .. attribute:: hidden

        Boolean to determine whether or not this column should be displayed
        when rendering the table. Default: ``False``.

    .. attribute:: link

        A string or callable which returns a URL which will be wrapped around
        this column's text as a link.

    .. attribute:: allowed_data_types

        A list of data types for which the link should be created.
        Default is an empty list (``[]``).

        When the list is empty and the ``link`` attribute is not None, all the
        rows under this column will be links.

    .. attribute::  status

        Boolean designating whether or not this column represents a status
        (i.e. "enabled/disabled", "up/down", "active/inactive").
        Default: ``False``.

    .. attribute::  status_choices

        A tuple of tuples representing the possible data values for the
        status column and their associated boolean equivalent. Positive
        states should equate to ``True``, negative states should equate
        to ``False``, and indeterminate states should be ``None``.

        Values are compared in a case-insensitive manner.

        Example (these are also the default values)::

            status_choices = (
                    ('enabled', True),
                    ('true', True),
                    ('up', True),
                    ('active', True),
                    ('yes', True),
                    ('on', True),
                    ('none', None),
                    ('unknown', None),
                    ('', None),
                    ('disabled', False),
                    ('down', False),
                    ('false', False),
                    ('inactive', False),
                    ('no', False),
                    ('off', False),
                )

    .. attribute::  display_choices

        A tuple of tuples representing the possible values to substitute
        the data when displayed in the column cell.

    .. attribute:: empty_value

        A string or callable to be used for cells which have no data.
        Defaults to the string ``"-"``.

    .. attribute:: summation

        A string containing the name of a summation method to be used in
        the generation of a summary row for this column. By default the
        options are ``"sum"`` or ``"average"``, which behave as expected.
        Optional.

    .. attribute:: filters

        A list of functions (often template filters) to be applied to the
        value of the data for this column prior to output. This is effectively
        a shortcut for writing a custom ``transform`` function in simple cases.

    .. attribute:: classes

        An iterable of CSS classes which should be added to this column.
        Example: ``classes=('foo', 'bar')``.

    .. attribute:: attrs

        A dict of HTML attribute strings which should be added to this column.
        Example: ``attrs={"data-foo": "bar"}``.

    .. attribute:: cell_attributes_getter

       A callable to get the HTML attributes of a column cell depending
       on the data. For example, to add additional description or help
       information for data in a column cell (e.g. in Images panel, for the
       column 'format')::

            helpText = {
              'ARI':'Amazon Ramdisk Image',
              'QCOW2':'QEMU' Emulator'
              }

            getHoverHelp(data):
              text = helpText.get(data, None)
              if text:
                  return {'title': text}
              else:
                  return {}
            ...
            ...
            cell_attributes_getter = getHoverHelp

    .. attribute:: truncate

        An integer for the maximum length of the string in this column. If the
        length of the data in this column is larger than the supplied number,
        the data for this column will be truncated and an ellipsis will be
        appended to the truncated data.
        Defaults to ``None``.

    .. attribute:: link_classes

        An iterable of CSS classes which will be added when the column's text
        is displayed as a link.
        This is left for backward compatibility. Deprecated in favor of the
        link_attributes attribute.
        Example: ``link_classes=('link-foo', 'link-bar')``.
        Defaults to ``None``.

    .. attribute:: wrap_list

        Boolean value indicating whether the contents of this cell should be
        wrapped in a ``<ul></ul>`` tag. Useful in conjunction with Django's
        ``unordered_list`` template filter. Defaults to ``False``.

    .. attribute:: form_field

        A form field used for inline editing of the column. A django
        forms.Field can be used or django form.Widget can be used.

        Example: ``form_field=forms.CharField()``.
        Defaults to ``None``.

    .. attribute:: form_field_attributes

        The additional html attributes that will be rendered to form_field.
        Example: ``form_field_attributes={'class': 'bold_input_field'}``.
        Defaults to ``None``.

    .. attribute:: update_action

        The class that inherits from tables.actions.UpdateAction, update_cell
        method takes care of saving inline edited data. The tables.base.Row
        get_data method needs to be connected to table for obtaining the data.
        Example: ``update_action=UpdateCell``.
        Defaults to ``None``.

    .. attribute:: link_attrs

        A dict of HTML attribute strings which should be added when the
        column's text is displayed as a link.
        Examples:
        ``link_attrs={"data-foo": "bar"}``.
        ``link_attrs={"target": "_blank", "class": "link-foo link-bar"}``.
        Defaults to ``None``.

    .. attribute:: policy_rules

        List of scope and rule tuples to do policy checks on, the
        composition of which is (scope, rule)

        * scope: service type managing the policy for action
        * rule: string representing the action to be checked

        for a policy that requires a single rule check,
        policy_rules should look like:

        .. code-block:: none

            "(("compute", "compute:create_instance"),)"

        for a policy that requires multiple rule checks,
        rules should look like:

        .. code-block:: none

            "(("identity", "identity:list_users"),
              ("identity", "identity:list_roles"))"

    .. attribute:: help_text

        A string of simple help text displayed in a tooltip when you hover
        over the help icon beside the Column name. Defaults to ``None``.
    """
    summation_methods = {
        "sum": sum,
        "average": lambda data: sum(data, 0.0) / len(data)
    }
    # Used to retain order when instantiating columns on a table
    creation_counter = 0

    transform = None
    name = None
    verbose_name = None
    status_choices = (
        ('enabled', True),
        ('true', True),
        ('up', True),
        ('yes', True),
        ('active', True),
        ('on', True),
        ('none', None),
        ('unknown', None),
        ('', None),
        ('disabled', False),
        ('down', False),
        ('false', False),
        ('inactive', False),
        ('no', False),
        ('off', False),
    )

    def __init__(self, transform, verbose_name=None, sortable=True,
                 link=None, allowed_data_types=None, hidden=False, attrs=None,
                 status=False, status_choices=None, display_choices=None,
                 empty_value=None, filters=None, classes=None, summation=None,
                 auto=None, truncate=None, link_classes=None, wrap_list=False,
                 form_field=None, form_field_attributes=None,
                 update_action=None, link_attrs=None, policy_rules=None,
                 cell_attributes_getter=None, help_text=None):

        allowed_data_types = allowed_data_types or []
        self.classes = list(classes or getattr(self, "classes", []))
        super(Column, self).__init__()
        self.attrs.update(attrs or {})

        if callable(transform):
            self.transform = transform
            self.name = "<%s callable>" % transform.__name__
        else:
            self.transform = six.text_type(transform)
            self.name = self.transform

        # Empty string is a valid value for verbose_name
        if verbose_name is None:
            if callable(transform):
                self.verbose_name = ''
            else:
                self.verbose_name = self.transform.title()
        else:
            self.verbose_name = verbose_name

        self.auto = auto
        self.sortable = sortable
        self.link = link
        self.allowed_data_types = allowed_data_types
        self.hidden = hidden
        self.status = status
        self.empty_value = empty_value or _('-')
        self.filters = filters or []
        self.truncate = truncate
        self.wrap_list = wrap_list
        self.form_field = form_field
        self.form_field_attributes = form_field_attributes or {}
        self.update_action = update_action
        self.link_attrs = link_attrs or {}
        self.policy_rules = policy_rules or []
        self.help_text = help_text
        if link_classes:
            self.link_attrs['class'] = ' '.join(link_classes)
        self.cell_attributes_getter = cell_attributes_getter

        if status_choices:
            self.status_choices = status_choices
        self.display_choices = display_choices

        if summation is not None and summation not in self.summation_methods:
            raise ValueError(
                "Summation method %(summation)s must be one of %(keys)s." %
                {'summation': summation,
                 'keys': ", ".join(self.summation_methods.keys())})
        self.summation = summation

        self.creation_counter = Column.creation_counter
        Column.creation_counter += 1

        if self.sortable and not self.auto:
            self.classes.append("sortable")
        if self.hidden:
            self.classes.append("hide")
        if self.link is not None:
            self.classes.append('anchor')

    def __str__(self):
        return six.text_type(self.verbose_name)

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.name)

    def allowed(self, request):
        """Determine whether processing/displaying the column is allowed.

        It is determined based on the current request.
        """
        if not self.policy_rules:
            return True

        policy_check = utils_settings.import_setting("POLICY_CHECK_FUNCTION")

        if policy_check:
            return policy_check(self.policy_rules, request)
        return True

    def get_raw_data(self, datum):
        """Returns the raw data for this column.

        No filters or formatting are applied to the returned data.
        This is useful when doing calculations on data in the table.
        """
        # Callable transformations
        if callable(self.transform):
            data = self.transform(datum)
        # Dict lookups
        elif isinstance(datum, Mapping) and self.transform in datum:
            data = datum.get(self.transform)
        else:
            # Basic object lookups
            data = getattr(datum, self.transform, None)
            if not hasattr(datum, self.transform):
                msg = "The attribute %(attr)s doesn't exist on %(obj)s."
                LOG.debug(termcolors.colorize(msg, **PALETTE['ERROR']),
                          {'attr': self.transform, 'obj': datum})
        return data

    def get_data(self, datum):
        """Returns the final display data for this column from the given inputs.

        The return value will be either the attribute specified for this column
        or the return value of the attr:`~horizon.tables.Column.transform`
        method for this column.
        """
        datum_id = self.table.get_object_id(datum)

        if datum_id in self.table._data_cache[self]:
            return self.table._data_cache[self][datum_id]

        data = self.get_raw_data(datum)
        display_value = None

        if self.display_choices:
            display_value = [display for (value, display) in
                             self.display_choices
                             if value.lower() == (data or '').lower()]

        if display_value:
            data = display_value[0]
        else:
            for filter_func in self.filters:
                try:
                    data = filter_func(data)
                except Exception:
                    msg = ("Filter '%(filter)s' failed with data "
                           "'%(data)s' on column '%(col_name)s'")
                    args = {'filter': filter_func.__name__,
                            'data': data,
                            'col_name': six.text_type(self.verbose_name)}
                    LOG.warning(msg, args)

        if data and self.truncate:
            data = truncatechars(data, self.truncate)

        self.table._data_cache[self][datum_id] = data

        return self.table._data_cache[self][datum_id]

    def get_link_url(self, datum):
        """Returns the final value for the column's ``link`` property.

        If ``allowed_data_types`` of this column  is not empty and the datum
        has an assigned type, check if the datum's type is in the
        ``allowed_data_types`` list. If not, the datum won't be displayed
        as a link.

        If ``link`` is a callable, it will be passed the current data object
        and should return a URL. Otherwise ``get_link_url`` will attempt to
        call ``reverse`` on ``link`` with the object's id as a parameter.
        Failing that, it will simply return the value of ``link``.
        """
        if self.allowed_data_types:
            data_type_name = self.table._meta.data_type_name
            data_type = getattr(datum, data_type_name, None)
            if data_type and (data_type not in self.allowed_data_types):
                return None
        obj_id = self.table.get_object_id(datum)
        if callable(self.link):
            if 'request' in getargspec(self.link).args:
                return self.link(datum, request=self.table.request)
            return self.link(datum)
        try:
            return urls.reverse(self.link, args=(obj_id,))
        except urls.NoReverseMatch:
            return self.link

    if settings.INTEGRATION_TESTS_SUPPORT:
        def get_default_attrs(self):
            attrs = super(Column, self).get_default_attrs()
            attrs.update({'data-selenium': self.name})
            return attrs

    def get_summation(self):
        """Returns the summary value for the data in this column.

        It returns the summary value if a valid summation method is
        specified for it. Otherwise returns ``None``.
        """
        if self.summation not in self.summation_methods:
            return None

        summation_function = self.summation_methods[self.summation]
        data = [self.get_raw_data(datum) for datum in self.table.data]
        data = [raw_data for raw_data in data if raw_data is not None]

        if data:
            try:
                summation = summation_function(data)
                for filter_func in self.filters:
                    summation = filter_func(summation)
                return summation
            except TypeError:
                pass
        return None


class WrappingColumn(Column):
    """A column that wraps its contents. Useful for data like UUIDs or names"""

    def __init__(self, *args, **kwargs):
        super(WrappingColumn, self).__init__(*args, **kwargs)
        self.classes.append('word-break')


class Row(html.HTMLElement):
    """Represents a row in the table.

    When iterated, the ``Row`` instance will yield each of its cells.

    Rows are capable of AJAX updating, with a little added work:

    The ``ajax`` property needs to be set to ``True``, and
    subclasses need to define a ``get_data`` method which returns a data
    object appropriate for consumption by the table (effectively the "get"
    lookup versus the table's "list" lookup).

    The automatic update interval is configurable by setting the key
    ``ajax_poll_interval`` in the ``HORIZON_CONFIG`` dictionary.
    Default: ``2500`` (measured in milliseconds).

    .. attribute:: table

        The table which this row belongs to.

    .. attribute:: datum

        The data object which this row represents.

    .. attribute:: id

        A string uniquely representing this row composed of the table name
        and the row data object's identifier.

    .. attribute:: cells

        The cells belonging to this row stored in a ``OrderedDict`` object.
        This attribute is populated during instantiation.

    .. attribute:: status

        Boolean value representing the status of this row calculated from
        the values of the table's ``status_columns`` if they are set.

    .. attribute:: status_class

        Returns a css class for the status of the row based on ``status``.

    .. attribute:: ajax

        Boolean value to determine whether ajax updating for this row is
        enabled.

    .. attribute:: ajax_action_name

        String that is used for the query parameter key to request AJAX
        updates. Generally you won't need to change this value.
        Default: ``"row_update"``.

    .. attribute:: ajax_cell_action_name

        String that is used for the query parameter key to request AJAX
        updates of cell. Generally you won't need to change this value.
        It is also used for inline edit of the cell.
        Default: ``"cell_update"``.
    """
    ajax = False
    ajax_action_name = "row_update"
    ajax_cell_action_name = "cell_update"

    def __init__(self, table, datum=None):
        super(Row, self).__init__()
        self.table = table
        self.datum = datum
        self.selected = False
        if self.datum:
            self.load_cells()
        else:
            self.id = None
            self.cells = []

    def load_cells(self, datum=None):
        """Load the row's data and initialize all the cells in the row.

        It also set the appropriate row properties which require
        the row's data to be determined.

        The row's data is provided either at initialization or as an
        argument to this function.

        This function is called automatically by
        :meth:`~horizon.tables.Row.__init__` if the ``datum`` argument is
        provided. However, by not providing the data during initialization
        this function allows for the possibility of a two-step loading
        pattern when you need a row instance but don't yet have the data
        available.
        """
        # Compile all the cells on instantiation.
        table = self.table
        if datum:
            self.datum = datum
        else:
            datum = self.datum
        cells = []
        for column in table.columns.values():
            cell = table._meta.cell_class(datum, column, self)
            cells.append((column.name or column.auto, cell))
        self.cells = collections.OrderedDict(cells)

        if self.ajax:
            interval = conf.HORIZON_CONFIG['ajax_poll_interval']
            self.attrs['data-update-interval'] = interval
            self.attrs['data-update-url'] = self.get_ajax_update_url()
            self.classes.append("ajax-update")

        self.attrs['data-object-id'] = table.get_object_id(datum)

        # Add the row's status class and id to the attributes to be rendered.
        self.classes.append(self.status_class)
        id_vals = {"table": self.table.name,
                   "sep": STRING_SEPARATOR,
                   "id": table.get_object_id(datum)}
        self.id = "%(table)s%(sep)srow%(sep)s%(id)s" % id_vals
        self.attrs['id'] = self.id

        # Add the row's display name if available
        display_name = table.get_object_display(datum)
        display_name_key = table.get_object_display_key(datum)

        if display_name:
            self.attrs['data-display'] = escape(display_name)
            self.attrs['data-display-key'] = escape(display_name_key)

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.id)

    def __iter__(self):
        return iter(self.cells.values())

    @property
    def status(self):
        column_names = self.table._meta.status_columns
        if column_names:
            statuses = dict((column_name, self.cells[column_name].status) for
                            column_name in column_names)
            return self.table.calculate_row_status(statuses)

    @property
    def status_class(self):
        column_names = self.table._meta.status_columns
        if column_names:
            return self.table.get_row_status_class(self.status)
        else:
            return ''

    def render(self):
        return render_to_string("horizon/common/_data_table_row.html",
                                {"row": self})

    def get_cells(self):
        """Returns the bound cells for this row in order."""
        return list(self.cells.values())

    def get_ajax_update_url(self):
        table_url = self.table.get_absolute_url()
        marker_name = self.table._meta.pagination_param
        marker = self.table.request.GET.get(marker_name, None)
        if not marker:
            marker_name = self.table._meta.prev_pagination_param
            marker = self.table.request.GET.get(marker_name, None)
        request_params = [
            ("action", self.ajax_action_name),
            ("table", self.table.name),
            ("obj_id", self.table.get_object_id(self.datum)),
        ]
        if marker:
            request_params.append((marker_name, marker))
        params = urlencode(collections.OrderedDict(request_params))
        return "%s?%s" % (table_url, params)

    def can_be_selected(self, datum):
        """Determines whether the row can be selected.

        By default if multiselect enabled return True.
        You can remove the checkbox after an ajax update here if required.
        """
        return True

    def get_data(self, request, obj_id):
        """Fetches the updated data for the row based on the given object ID.

        Must be implemented by a subclass to allow AJAX updating.
        """
        return {}


class Cell(html.HTMLElement):
    """Represents a single cell in the table."""

    def __init__(self, datum, column, row, attrs=None, classes=None):
        self.classes = classes or getattr(self, "classes", [])
        super(Cell, self).__init__()
        self.attrs.update(attrs or {})

        self.datum = datum
        self.column = column
        self.row = row
        self.wrap_list = column.wrap_list
        self.inline_edit_available = self.column.update_action is not None
        # initialize the update action if available
        if self.inline_edit_available:
            self.update_action = self.column.update_action()
            self.attrs['data-cell-name'] = column.name
            self.attrs['data-update-url'] = self.get_ajax_update_url()
        self.inline_edit_mod = False
        # add tooltip to cells if the truncate variable is set
        if column.truncate:
            # NOTE(tsufiev): trying to pull cell raw data out of datum for
            # those columns where truncate is False leads to multiple errors
            # in unit tests
            data = getattr(datum, column.name, '') or ''
            data = encoding.force_text(data)
            if len(data) > column.truncate:
                self.attrs['data-toggle'] = 'tooltip'
                self.attrs['title'] = data
                if settings.INTEGRATION_TESTS_SUPPORT:
                    self.attrs['data-selenium'] = data
        self.data = self.get_data(datum, column, row)

    def get_data(self, datum, column, row):
        """Fetches the data to be displayed in this cell."""
        table = row.table
        if column.auto == "multi_select":
            data = ""
            if row.can_be_selected(datum):
                widget = ThemableCheckboxInput(check_test=lambda value: False)
                # Convert value to string to avoid accidental type conversion
                data = widget.render('object_ids',
                                     six.text_type(table.get_object_id(datum)),
                                     {'class': 'table-row-multi-select'})
            table._data_cache[column][table.get_object_id(datum)] = data
        elif column.auto == "form_field":
            widget = column.form_field
            if issubclass(widget.__class__, forms.Field):
                widget = widget.widget

            widget_name = "%s__%s" % \
                (column.name,
                 six.text_type(table.get_object_id(datum)))

            # Create local copy of attributes, so it don't change column
            # class form_field_attributes
            form_field_attributes = {}
            form_field_attributes.update(column.form_field_attributes)
            # Adding id of the input so it pairs with label correctly
            form_field_attributes['id'] = widget_name

            if (template.defaultfilters.urlize in column.filters or
                    template.defaultfilters.yesno in column.filters):
                data = widget.render(widget_name,
                                     column.get_raw_data(datum),
                                     form_field_attributes)
            else:
                data = widget.render(widget_name,
                                     column.get_data(datum),
                                     form_field_attributes)
            table._data_cache[column][table.get_object_id(datum)] = data
        elif column.auto == "actions":
            data = table.render_row_actions(datum)
            table._data_cache[column][table.get_object_id(datum)] = data
        else:
            data = column.get_data(datum)
            if column.cell_attributes_getter:
                cell_attributes = column.cell_attributes_getter(data) or {}
                self.attrs.update(cell_attributes)
        return data

    def __repr__(self):
        return '<%s: %s, %s>' % (self.__class__.__name__,
                                 self.column.name,
                                 self.row.id)

    @property
    def id(self):
        return ("%s__%s" % (self.column.name,
                six.text_type(self.row.table.get_object_id(self.datum))))

    @property
    def value(self):
        """Returns a formatted version of the data for final output.

        This takes into consideration the
        :attr:`~horizon.tables.Column.link`` and
        :attr:`~horizon.tables.Column.empty_value`
        attributes.
        """
        try:
            data = self.column.get_data(self.datum)
            if data is None:
                if callable(self.column.empty_value):
                    data = self.column.empty_value(self.datum)
                else:
                    data = self.column.empty_value
        except Exception:
            data = None
            exc_info = sys.exc_info()
            raise six.reraise(template.TemplateSyntaxError, exc_info[1],
                              exc_info[2])

        if self.url and not self.column.auto == "form_field":
            link_attrs = ' '.join(['%s="%s"' % (k, v) for (k, v) in
                                  self.column.link_attrs.items()])
            # Escape the data inside while allowing our HTML to render
            data = mark_safe('<a href="%s" %s>%s</a>' % (
                             (escape(self.url),
                              link_attrs,
                              escape(six.text_type(data)))))
        return data

    @property
    def url(self):
        if self.column.link:
            url = self.column.get_link_url(self.datum)
            if url:
                return url
        else:
            return None

    @property
    def status(self):
        """Gets the status for the column based on the cell's data."""
        # Deal with status column mechanics based in this cell's data
        if hasattr(self, '_status'):
            # pylint: disable=access-member-before-definition
            return self._status

        if self.column.status or \
                self.column.name in self.column.table._meta.status_columns:
            # returns the first matching status found
            data_status_lower = six.text_type(
                self.column.get_raw_data(self.datum)).lower()
            for status_name, status_value in self.column.status_choices:
                if six.text_type(status_name).lower() == data_status_lower:
                    self._status = status_value
                    return self._status
        self._status = None
        return self._status

    def get_status_class(self, status):
        """Returns a css class name determined by the status value."""
        if status is True:
            return "status_up"
        elif status is False:
            return "status_down"
        else:
            return "warning"

    def get_default_classes(self):
        """Returns a flattened string of the cell's CSS classes."""
        if not self.url:
            self.column.classes = [cls for cls in self.column.classes
                                   if cls != "anchor"]
        column_class_string = self.column.get_final_attrs().get('class', "")
        classes = set(column_class_string.split(" "))
        if self.column.status:
            classes.add(self.get_status_class(self.status))

        if self.inline_edit_available:
            classes.add("inline_edit_available")

        return list(classes)

    def get_ajax_update_url(self):
        column = self.column
        table_url = column.table.get_absolute_url()
        params = urlencode(collections.OrderedDict([
            ("action", self.row.ajax_cell_action_name),
            ("table", column.table.name),
            ("cell_name", column.name),
            ("obj_id", column.table.get_object_id(self.datum))
        ]))

        return "%s?%s" % (table_url, params)

    @property
    def update_allowed(self):
        """Determines whether update of given cell is allowed.

        Calls allowed action of defined UpdateAction of the Column.
        """
        return self.update_action.allowed(self.column.table.request,
                                          self.datum,
                                          self)

    def render(self):
        return render_to_string("horizon/common/_data_table_cell.html",
                                {"cell": self})


class DataTableOptions(object):
    """Contains options for :class:`.DataTable` objects.

    .. attribute:: name

        A short name or slug for the table.

    .. attribute:: verbose_name

        A more verbose name for the table meant for display purposes.

    .. attribute:: columns

        A list of column objects or column names. Controls ordering/display
        of the columns in the table.

    .. attribute:: table_actions

        A list of action classes derived from the
        :class:`~horizon.tables.Action` class. These actions will handle tasks
        such as bulk deletion, etc. for multiple objects at once.

    .. attribute:: table_actions_menu

        A list of action classes similar to ``table_actions`` except these
        will be displayed in a menu instead of as individual buttons. Actions
        from this list will take precedence over actions from the
        ``table_actions`` list.

    .. attribute:: table_actions_menu_label

        A label of a menu button for ``table_actions_menu``. The default is
        "Actions" or "More Actions" depending on ``table_actions``.

    .. attribute:: row_actions

        A list similar to ``table_actions`` except tailored to appear for
        each row. These actions act on a single object at a time.

    .. attribute:: actions_column

        Boolean value to control rendering of an additional column containing
        the various actions for each row. Defaults to ``True`` if any actions
        are specified in the ``row_actions`` option.

    .. attribute:: multi_select

        Boolean value to control rendering of an extra column with checkboxes
        for selecting multiple objects in the table. Defaults to ``True`` if
        any actions are specified in the ``table_actions`` option.

    .. attribute:: filter

        Boolean value to control the display of the "filter" search box
        in the table actions. By default it checks whether or not an instance
        of :class:`.FilterAction` is in ``table_actions``.

    .. attribute:: template

        String containing the template which should be used to render the
        table. Defaults to ``"horizon/common/_data_table.html"``.

    .. attribute:: row_actions_dropdown_template

        String containing the template which should be used to render the
        row actions dropdown. Defaults to
        ``"horizon/common/_data_table_row_actions_dropdown.html"``.

    .. attribute:: row_actions_row_template

        String containing the template which should be used to render the
        row actions. Defaults to
        ``"horizon/common/_data_table_row_actions_row.html"``.

    .. attribute:: table_actions_template

        String containing the template which should be used to render the
        table actions. Defaults to
        ``"horizon/common/_data_table_table_actions.html"``.

    .. attribute:: context_var_name

        The name of the context variable which will contain the table when
        it is rendered. Defaults to ``"table"``.

    .. attribute:: prev_pagination_param

        The name of the query string parameter which will be used when
        paginating backward in this table. When using multiple tables in a
        single view this will need to be changed to differentiate between the
        tables. Default: ``"prev_marker"``.

    .. attribute:: pagination_param

        The name of the query string parameter which will be used when
        paginating forward in this table. When using multiple tables in a
        single view this will need to be changed to differentiate between the
        tables. Default: ``"marker"``.

    .. attribute:: status_columns

        A list or tuple of column names which represents the "state"
        of the data object being represented.

        If ``status_columns`` is set, when the rows are rendered the value
        of this column will be used to add an extra class to the row in
        the form of ``"status_up"`` or ``"status_down"`` for that row's
        data.

        The row status is used by other Horizon components to trigger tasks
        such as dynamic AJAX updating.

    .. attribute:: cell_class

        The class which should be used for rendering the cells of this table.
        Optional. Default: :class:`~horizon.tables.Cell`.

    .. attribute:: row_class

        The class which should be used for rendering the rows of this table.
        Optional. Default: :class:`~horizon.tables.Row`.

    .. attribute:: column_class

        The class which should be used for handling the columns of this table.
        Optional. Default: :class:`~horizon.tables.Column`.

    .. attribute:: css_classes

        A custom CSS class or classes to add to the ``<table>`` tag of the
        rendered table, for when the particular table requires special styling.
        Default: ``""``.

    .. attribute:: mixed_data_type

        A toggle to indicate if the table accepts two or more types of data.
        Optional. Default: ``False``

    .. attribute:: data_types

        A list of data types that this table would accept. Default to be an
        empty list, but if the attribute ``mixed_data_type`` is set to
        ``True``, then this list must have at least one element.

    .. attribute:: data_type_name

        The name of an attribute to assign to data passed to the table when it
        accepts mix data. Default: ``"_table_data_type"``

    .. attribute:: footer

        Boolean to control whether or not to show the table's footer.
        Default: ``True``.

    .. attribute:: hidden_title

        Boolean to control whether or not to show the table's title.
        Default: ``True``.

    .. attribute:: permissions

        A list of permission names which this table requires in order to be
        displayed. Defaults to an empty list (``[]``).
    """
    def __init__(self, options):
        self.name = getattr(options, 'name', self.__class__.__name__)
        verbose_name = (getattr(options, 'verbose_name', None) or
                        self.name.title())
        self.verbose_name = verbose_name
        self.columns = getattr(options, 'columns', None)
        self.status_columns = getattr(options, 'status_columns', [])
        self.table_actions = getattr(options, 'table_actions', [])
        self.row_actions = getattr(options, 'row_actions', [])
        self.table_actions_menu = getattr(options, 'table_actions_menu', [])
        self.table_actions_menu_label = getattr(options,
                                                'table_actions_menu_label',
                                                None)
        self.cell_class = getattr(options, 'cell_class', Cell)
        self.row_class = getattr(options, 'row_class', Row)
        self.column_class = getattr(options, 'column_class', Column)
        self.css_classes = getattr(options, 'css_classes', '')
        self.prev_pagination_param = getattr(options,
                                             'prev_pagination_param',
                                             'prev_marker')
        self.pagination_param = getattr(options, 'pagination_param', 'marker')
        self.browser_table = getattr(options, 'browser_table', None)
        self.footer = getattr(options, 'footer', True)
        self.hidden_title = getattr(options, 'hidden_title', True)
        self.no_data_message = getattr(options,
                                       "no_data_message",
                                       _("No items to display."))
        self.permissions = getattr(options, 'permissions', [])

        # Set self.filter if we have any FilterActions
        filter_actions = [action for action in self.table_actions if
                          issubclass(action, FilterAction)]
        batch_actions = [action for action in self.table_actions if
                         issubclass(action, BatchAction)]
        if len(filter_actions) > 1:
            raise NotImplementedError("Multiple filter actions are not "
                                      "currently supported.")
        self.filter = getattr(options, 'filter', len(filter_actions) > 0)
        if len(filter_actions) == 1:
            self._filter_action = filter_actions.pop()
        else:
            self._filter_action = None

        self.template = getattr(options,
                                'template',
                                'horizon/common/_data_table.html')
        self.row_actions_dropdown_template = \
            getattr(options,
                    'row_actions_dropdown_template',
                    'horizon/common/_data_table_row_actions_dropdown.html')
        self.row_actions_row_template = \
            getattr(options,
                    'row_actions_row_template',
                    'horizon/common/_data_table_row_actions_row.html')
        self.table_actions_template = \
            getattr(options,
                    'table_actions_template',
                    'horizon/common/_data_table_table_actions.html')
        self.context_var_name = six.text_type(getattr(options,
                                                      'context_var_name',
                                                      'table'))
        self.actions_column = getattr(options,
                                      'actions_column',
                                      len(self.row_actions) > 0)
        self.multi_select = getattr(options,
                                    'multi_select',
                                    len(batch_actions) > 0)

        # Set runtime table defaults; not configurable.
        self.has_prev_data = False
        self.has_more_data = False

        # Set mixed data type table attr
        self.mixed_data_type = getattr(options, 'mixed_data_type', False)
        self.data_types = getattr(options, 'data_types', [])

        # If the data_types has more than 2 elements, set mixed_data_type
        # to True automatically.
        if len(self.data_types) > 1:
            self.mixed_data_type = True

        # However, if the mixed_data_type is set to True manually and
        # the data_types is empty, raise an error.
        if self.mixed_data_type and len(self.data_types) <= 1:
            raise ValueError("If mixed_data_type is set to True in class %s, "
                             "data_types should has more than one types" %
                             self.name)

        self.data_type_name = getattr(options,
                                      'data_type_name',
                                      "_table_data_type")

        self.filter_first_message = \
            getattr(options,
                    'filter_first_message',
                    _('Please specify a search criteria first.'))


class DataTableMetaclass(type):
    """Metaclass to add options to DataTable class and collect columns."""
    def __new__(cls, name, bases, attrs):
        # Process options from Meta
        class_name = name
        dt_attrs = {}
        dt_attrs["_meta"] = opts = DataTableOptions(attrs.get("Meta", None))

        # Gather columns; this prevents the column from being an attribute
        # on the DataTable class and avoids naming conflicts.
        columns = []
        for attr_name, obj in attrs.items():
            if isinstance(obj, (opts.column_class, Column)):
                column_instance = attrs[attr_name]
                column_instance.name = attr_name
                column_instance.classes.append('normal_column')
                columns.append((attr_name, column_instance))
            else:
                dt_attrs[attr_name] = obj
        columns.sort(key=lambda x: x[1].creation_counter)

        # Iterate in reverse to preserve final order
        for base in reversed(bases):
            if hasattr(base, 'base_columns'):
                columns[0:0] = base.base_columns.items()
        dt_attrs['base_columns'] = collections.OrderedDict(columns)

        # If the table is in a ResourceBrowser, the column number must meet
        # these limits because of the width of the browser.
        if opts.browser_table == "navigation" and len(columns) > 3:
            raise ValueError("You can assign at most three columns to %s."
                             % class_name)
        if opts.browser_table == "content" and len(columns) > 2:
            raise ValueError("You can assign at most two columns to %s."
                             % class_name)

        if opts.columns:
            # Remove any columns that weren't declared if we're being explicit
            # NOTE: we're iterating a COPY of the list here!
            for column_data in columns[:]:
                if column_data[0] not in opts.columns:
                    columns.pop(columns.index(column_data))
            # Re-order based on declared columns
            columns.sort(key=lambda x: dt_attrs['_meta'].columns.index(x[0]))
        # Add in our auto-generated columns
        if opts.multi_select and opts.browser_table != "navigation":
            multi_select = opts.column_class("multi_select",
                                             verbose_name="",
                                             auto="multi_select")
            multi_select.classes.append('multi_select_column')
            columns.insert(0, ("multi_select", multi_select))
        if opts.actions_column:
            actions_column = opts.column_class("actions",
                                               verbose_name=_("Actions"),
                                               auto="actions")
            actions_column.classes.append('actions_column')
            columns.append(("actions", actions_column))
        # Store this set of columns internally so we can copy them per-instance
        dt_attrs['_columns'] = collections.OrderedDict(columns)

        # Gather and register actions for later access since we only want
        # to instantiate them once.
        # (list() call gives deterministic sort order, which sets don't have.)
        actions = list(set(opts.row_actions) | set(opts.table_actions) |
                       set(opts.table_actions_menu))
        actions.sort(key=attrgetter('name'))
        actions_dict = collections.OrderedDict([(action.name, action())
                                                for action in actions])
        dt_attrs['base_actions'] = actions_dict
        if opts._filter_action:
            # Replace our filter action with the instantiated version
            opts._filter_action = actions_dict[opts._filter_action.name]

        # Create our new class!
        return type.__new__(cls, name, bases, dt_attrs)


@six.python_2_unicode_compatible
@six.add_metaclass(DataTableMetaclass)
class DataTable(object):
    """A class which defines a table with all data and associated actions.

    .. attribute:: name

        String. Read-only access to the name specified in the
        table's Meta options.

    .. attribute:: multi_select

        Boolean. Read-only access to whether or not this table
        should display a column for multi-select checkboxes.

    .. attribute:: data

        Read-only access to the data this table represents.

    .. attribute:: filtered_data

        Read-only access to the data this table represents, filtered by
        the :meth:`~horizon.tables.FilterAction.filter` method of the table's
        :class:`~horizon.tables.FilterAction` class (if one is provided)
        using the current request's query parameters.
    """

    def __init__(self, request, data=None, needs_form_wrapper=None, **kwargs):
        self.request = request
        self.data = data
        self.kwargs = kwargs
        self._needs_form_wrapper = needs_form_wrapper
        self._no_data_message = self._meta.no_data_message
        self.breadcrumb = None
        self.current_item_id = None
        self.permissions = self._meta.permissions
        self.needs_filter_first = False
        self._filter_first_message = self._meta.filter_first_message

        # Create a new set
        columns = []
        for key, _column in self._columns.items():
            if _column.allowed(request):
                column = copy.copy(_column)
                column.table = self
                columns.append((key, column))
        self.columns = collections.OrderedDict(columns)
        self._populate_data_cache()

        # Associate these actions with this table
        for action in self.base_actions.values():
            action.associate_with_table(self)

        self.needs_summary_row = any([col.summation
                                      for col in self.columns.values()])
        # For multi-process, we need to set the multi_column to be visible
        # or hidden each time.
        # Example: first process the multi_column visible but second
        # process the column is hidden. Updating row by ajax will
        # make the bug#1799151
        if request.GET.get('action') == 'row_update':
            bound_actions = self.get_table_actions()
            batch_actions = [action for action in bound_actions
                             if isinstance(action, BatchAction)]
            self.set_multiselect_column_visibility(bool(batch_actions))

    def __str__(self):
        return six.text_type(self._meta.verbose_name)

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self._meta.name)

    @property
    def name(self):
        return self._meta.name

    @property
    def footer(self):
        return self._meta.footer

    @property
    def multi_select(self):
        return self._meta.multi_select

    @property
    def filtered_data(self):
        # This function should be using django.utils.functional.cached_property
        # decorator, but unfortunately due to bug in Django
        # https://code.djangoproject.com/ticket/19872 it would make it fail
        # when being mocked in tests.
        # TODO(amotoki): Check if this trick is still required.
        if not hasattr(self, '_filtered_data'):
            self._filtered_data = self.data
            if self._meta.filter and self._meta._filter_action:
                action = self._meta._filter_action
                filter_string = self.get_filter_string()
                filter_field = self.get_filter_field()
                request_method = self.request.method
                needs_preloading = (not filter_string and
                                    request_method == 'GET' and
                                    action.needs_preloading)
                valid_method = (request_method == action.method)
                not_api_filter = (filter_string and
                                  not action.is_api_filter(filter_field))

                if valid_method or needs_preloading or not_api_filter:
                    if self._meta.mixed_data_type:
                        self._filtered_data = action.data_type_filter(
                            self, self.data, filter_string)
                    else:
                        self._filtered_data = action.filter(
                            self, self.data, filter_string)
        return self._filtered_data

    def slugify_name(self):
        return str(slugify(self._meta.name))

    def get_filter_string(self):
        """Get the filter string value.

        For 'server' type filters this is saved in the session so that
        it gets persisted across table loads.  For other filter types
        this is obtained from the POST dict.
        """
        filter_action = self._meta._filter_action
        param_name = filter_action.get_param_name()
        filter_string = ''
        if filter_action.filter_type == 'server':
            filter_string = self.request.session.get(param_name, '')
        else:
            filter_string = self.request.POST.get(param_name, '')
        return filter_string

    def get_filter_field(self):
        """Get the filter field value used for 'server' type filters.

        This is the value from the filter action's list of filter choices.
        """
        filter_action = self._meta._filter_action
        param_name = '%s_field' % filter_action.get_param_name()
        filter_field = self.request.session.get(param_name, '')
        return filter_field

    def _populate_data_cache(self):
        self._data_cache = {}
        # Set up hash tables to store data points for each column
        for column in self.get_columns():
            self._data_cache[column] = {}

    def _filter_action(self, action, request, datum=None):
        try:
            # Catch user errors in permission functions here
            row_matched = True
            if self._meta.mixed_data_type:
                row_matched = action.data_type_matched(datum)
            return action._allowed(request, datum) and row_matched
        except AssertionError:
            # don't trap mox exceptions (which subclass AssertionError)
            # when testing!
            # TODO(amotoki): Check if this trick is still required.
            raise
        except Exception:
            LOG.exception("Error while checking action permissions.")
            return None

    def is_browser_table(self):
        if self._meta.browser_table:
            return True
        return False

    def render(self):
        """Renders the table using the template from the table options."""
        table_template = template.loader.get_template(self._meta.template)
        extra_context = {self._meta.context_var_name: self,
                         'hidden_title': self._meta.hidden_title}
        return table_template.render(extra_context, self.request)

    def get_absolute_url(self):
        """Returns the canonical URL for this table.

        This is used for the POST action attribute on the form element
        wrapping the table. In many cases it is also useful for redirecting
        after a successful action on the table.

        For convenience it defaults to the value of
        ``request.get_full_path()`` with any query string stripped off,
        e.g. the path at which the table was requested.
        """
        return self.request.get_full_path().partition('?')[0]

    def get_full_url(self):
        """Returns the full URL path for this table.

        This is used for the POST action attribute on the form element
        wrapping the table. We use this method to persist the
        pagination marker.

        """
        return self.request.get_full_path()

    def get_empty_message(self):
        """Returns the message to be displayed when there is no data."""
        return self._no_data_message

    def get_filter_first_message(self):
        """Return the message to be displayed first in the filter.

        when the user needs to provide a search criteria first
        before loading any data.
        """
        return self._filter_first_message

    def get_object_by_id(self, lookup):
        """Returns the data object whose ID matches ``loopup`` parameter.

        The data object is looked up from the table's dataset and
        the data which matches the ``lookup`` parameter specified.
        An error will be raised if the match is not a single data object.

        We will convert the object id and ``lookup`` to unicode before
        comparison.

        Uses :meth:`~horizon.tables.DataTable.get_object_id` internally.
        """
        if not isinstance(lookup, six.text_type):
            lookup = str(lookup)
            if six.PY2:
                lookup = lookup.decode('utf-8')
        matches = []
        for datum in self.data:
            obj_id = self.get_object_id(datum)
            if not isinstance(obj_id, six.text_type):
                obj_id = str(obj_id)
                if six.PY2:
                    obj_id = obj_id.decode('utf-8')
            if obj_id == lookup:
                matches.append(datum)
        if len(matches) > 1:
            raise ValueError("Multiple matches were returned for that id: %s."
                             % matches)
        if not matches:
            raise exceptions.Http302(self.get_absolute_url(),
                                     _('No match returned for the id "%s".')
                                     % lookup)
        return matches[0]

    @property
    def has_actions(self):
        """Indicates whether there are any available actions on this table.

        Returns a boolean value.
        """
        if not self.base_actions:
            return False
        return any(self.get_table_actions()) or any(self._meta.row_actions)

    @property
    def needs_form_wrapper(self):
        """Returns if this table should be rendered wrapped in a ``<form>`` tag.

        Returns a boolean value.
        """
        # If needs_form_wrapper is explicitly set, defer to that.
        if self._needs_form_wrapper is not None:
            return self._needs_form_wrapper
        # Otherwise calculate whether or not we need a form element.
        return self.has_actions

    def get_table_actions(self):
        """Returns a list of the action instances for this table."""
        button_actions = [self.base_actions[action.name] for action in
                          self._meta.table_actions if
                          action not in self._meta.table_actions_menu]
        menu_actions = [self.base_actions[action.name] for
                        action in self._meta.table_actions_menu]
        bound_actions = button_actions + menu_actions
        return [action for action in bound_actions if
                self._filter_action(action, self.request)]

    def get_row_actions(self, datum):
        """Returns a list of the action instances for a specific row."""
        bound_actions = []
        for action in self._meta.row_actions:
            # Copy to allow modifying properties per row
            bound_action = copy.copy(self.base_actions[action.name])
            bound_action.attrs = copy.copy(bound_action.attrs)
            bound_action.datum = datum
            # Remove disallowed actions.
            if not self._filter_action(bound_action,
                                       self.request,
                                       datum):
                continue
            # Hook for modifying actions based on data. No-op by default.
            bound_action.update(self.request, datum)
            # Pre-create the URL for this link with appropriate parameters
            if issubclass(bound_action.__class__, LinkAction):
                bound_action.bound_url = bound_action.get_link_url(datum)
            bound_actions.append(bound_action)
        return bound_actions

    def set_multiselect_column_visibility(self, visible=True):
        """hide checkbox column if no current table action is allowed."""
        if not self.multi_select:
            return
        select_column = list(self.columns.values())[0]
        # Try to find if the hidden class need to be
        # removed or added based on visible flag.
        hidden_found = 'hidden' in select_column.classes
        if hidden_found and visible:
            select_column.classes.remove('hidden')
        elif not hidden_found and not visible:
            select_column.classes.append('hidden')

    def render_table_actions(self):
        """Renders the actions specified in ``Meta.table_actions``."""
        template_path = self._meta.table_actions_template
        table_actions_template = template.loader.get_template(template_path)
        bound_actions = self.get_table_actions()
        batch_actions = [action for action in bound_actions
                         if isinstance(action, BatchAction)]
        extra_context = {"table_actions": bound_actions,
                         "table_actions_buttons": [],
                         "table_actions_menu": []}
        if self._meta.filter and (
                self._filter_action(self._meta._filter_action, self.request)):
            extra_context["filter"] = self._meta._filter_action
        for action in bound_actions:
            if action.__class__ in self._meta.table_actions_menu:
                extra_context['table_actions_menu'].append(action)
            elif action != extra_context.get('filter'):
                extra_context['table_actions_buttons'].append(action)
        if self._meta.table_actions_menu_label:
            extra_context['table_actions_menu_label'] = \
                self._meta.table_actions_menu_label
        self.set_multiselect_column_visibility(bool(batch_actions))
        return table_actions_template.render(extra_context, self.request)

    def render_row_actions(self, datum, row=False):
        """Renders the actions specified in ``Meta.row_actions``.

        The actions are rendered using the current row data.
        If `row` is True, the actions are rendered in a row
        of buttons. Otherwise they are rendered in a dropdown box.
        """
        if row:
            template_path = self._meta.row_actions_row_template
        else:
            template_path = self._meta.row_actions_dropdown_template

        row_actions_template = template.loader.get_template(template_path)
        bound_actions = self.get_row_actions(datum)
        extra_context = {"row_actions": bound_actions,
                         "row_id": self.get_object_id(datum)}
        return row_actions_template.render(extra_context, self.request)

    @staticmethod
    def parse_action(action_string):
        """Parses the ``action_string`` parameter sent back with the POST data.

        By default this parses a string formatted as
        ``{{ table_name }}__{{ action_name }}__{{ row_id }}`` and returns
        each of the pieces. The ``row_id`` is optional.
        """
        if action_string:
            bits = action_string.split(STRING_SEPARATOR)
            table = bits[0]
            action = bits[1]
            try:
                object_id = STRING_SEPARATOR.join(bits[2:])
                if object_id == '':
                    object_id = None
            except IndexError:
                object_id = None
            return table, action, object_id

    def take_action(self, action_name, obj_id=None, obj_ids=None):
        """Locates the appropriate action and routes the object data to it.

        The action should return an HTTP redirect if successful,
        or a value which evaluates to ``False`` if unsuccessful.
        """
        # See if we have a list of ids
        obj_ids = obj_ids or self.request.POST.getlist('object_ids')
        action = self.base_actions.get(action_name, None)
        if not action or action.method != self.request.method:
            # We either didn't get an action or we're being hacked. Goodbye.
            return None

        # Meanwhile, back in Gotham...
        if not action.requires_input or obj_id or obj_ids:
            if obj_id:
                obj_id = self.sanitize_id(obj_id)
            if obj_ids:
                obj_ids = [self.sanitize_id(i) for i in obj_ids]
            # Single handling is easy
            if not action.handles_multiple:
                response = action.single(self, self.request, obj_id)
            # Otherwise figure out what to pass along
            else:
                # Preference given to a specific id, since that implies
                # the user selected an action for just one row.
                if obj_id:
                    obj_ids = [obj_id]
                response = action.multiple(self, self.request, obj_ids)
            return response
        elif action and action.requires_input and not (obj_id or obj_ids):
            messages.info(self.request,
                          _("Please select a row before taking that action."))
        return None

    @classmethod
    def check_handler(cls, request):
        """Determine whether the request should be handled by this table."""
        if request.method == "POST" and "action" in request.POST:
            table, action, obj_id = cls.parse_action(request.POST["action"])
        elif "table" in request.GET and "action" in request.GET:
            table = request.GET["table"]
            action = request.GET["action"]
            obj_id = request.GET.get("obj_id", None)
        else:
            table = action = obj_id = None
        return table, action, obj_id

    def maybe_preempt(self):
        """Determine whether the request should be handled in earlier phase.

        It determines the request should be handled by a preemptive action
        on this table or by an AJAX row update before loading any data.
        """
        request = self.request
        table_name, action_name, obj_id = self.check_handler(request)

        if table_name == self.name:
            # Handle AJAX row updating.
            new_row = self._meta.row_class(self)

            if new_row.ajax and new_row.ajax_action_name == action_name:
                try:
                    datum = new_row.get_data(request, obj_id)
                    if self.get_object_id(datum) == self.current_item_id:
                        self.selected = True
                        new_row.classes.append('current_selected')
                    new_row.load_cells(datum)
                    error = False
                except Exception:
                    datum = None
                    error = exceptions.handle(request, ignore=True)
                if request.is_ajax():
                    if not error:
                        return HttpResponse(new_row.render())
                    else:
                        return HttpResponse(status=error.status_code)
            elif new_row.ajax_cell_action_name == action_name:
                # inline edit of the cell actions
                return self.inline_edit_handle(request, table_name,
                                               action_name, obj_id,
                                               new_row)

            preemptive_actions = [action for action in
                                  self.base_actions.values() if action.preempt]
            if action_name:
                for action in preemptive_actions:
                    if action.name == action_name:
                        handled = self.take_action(action_name, obj_id)
                        if handled:
                            return handled
        return None

    def inline_edit_handle(self, request, table_name, action_name, obj_id,
                           new_row):
        """Inline edit handler.

        Showing form or handling update by POST of the cell.
        """
        try:
            cell_name = request.GET['cell_name']
            datum = new_row.get_data(request, obj_id)
            # TODO(lsmola) extract load cell logic to Cell and load
            # only 1 cell. This is kind of ugly.
            if request.GET.get('inline_edit_mod') == "true":
                new_row.table.columns[cell_name].auto = "form_field"
                inline_edit_mod = True
            else:
                inline_edit_mod = False

            # Load the cell and set the inline_edit_mod.
            new_row.load_cells(datum)
            cell = new_row.cells[cell_name]
            cell.inline_edit_mod = inline_edit_mod

            # If not allowed, neither edit mod or updating is allowed.
            if not cell.update_allowed:
                datum_display = (self.get_object_display(datum) or "N/A")
                LOG.info('Permission denied to Update Action: "%s"',
                         datum_display)
                return HttpResponse(status=401)
            # If it is post request, we are updating the cell.
            if request.method == "POST":
                return self.inline_update_action(request,
                                                 datum,
                                                 cell,
                                                 obj_id,
                                                 cell_name)

            error = False
        except Exception:
            datum = None
            error = exceptions.handle(request, ignore=True)
        if request.is_ajax():
            if not error:
                return HttpResponse(cell.render())
            else:
                return HttpResponse(status=error.status_code)

    def inline_update_action(self, request, datum, cell, obj_id, cell_name):
        """Handling update by POST of the cell."""
        new_cell_value = request.POST.get(
            cell_name + '__' + obj_id, None)
        if issubclass(cell.column.form_field.__class__,
                      forms.Field):
            try:
                # using Django Form Field to parse the
                # right value from POST and to validate it
                new_cell_value = (
                    cell.column.form_field.clean(
                        new_cell_value))
                cell.update_action.action(
                    self.request, datum, obj_id, cell_name, new_cell_value)
                response = {
                    'status': 'updated',
                    'message': ''
                }
                return HttpResponse(
                    json.dumps(response),
                    status=200,
                    content_type="application/json")

            except core_exceptions.ValidationError:
                # if there is a validation error, I will
                # return the message to the client
                exc_type, exc_value, exc_traceback = (
                    sys.exc_info())
                response = {
                    'status': 'validation_error',
                    'message': ' '.join(exc_value.messages)}
                return HttpResponse(
                    json.dumps(response),
                    status=400,
                    content_type="application/json")

    def maybe_handle(self):
        """Handles table actions if needed.

        It determines whether the request should be handled by any action on
        this table after data has been loaded.
        """
        request = self.request
        table_name, action_name, obj_id = self.check_handler(request)
        if table_name == self.name and action_name:
            action_names = [action.name for action in
                            self.base_actions.values() if not action.preempt]
            # do not run preemptive actions here
            if action_name in action_names:
                return self.take_action(action_name, obj_id)
        return None

    def sanitize_id(self, obj_id):
        """Override to modify an incoming obj_id to match existing API.

        It is used to modify an incoming obj_id (used in Horizon)
        to the data type or format expected by the API.
        """
        return obj_id

    def get_object_id(self, datum):
        """Returns the identifier for the object this row will represent.

        By default this returns an ``id`` attribute on the given object,
        but this can be overridden to return other values.

        .. warning::

            Make sure that the value returned is a unique value for the id
            otherwise rendering issues can occur.
        """
        return datum.id

    def get_object_display_key(self, datum):
        return 'name'

    def get_object_display(self, datum):
        """Returns a display name that identifies this object.

        By default, this returns a ``name`` attribute from the given object,
        but this can be overridden to return other values.
        """
        display_key = self.get_object_display_key(datum)
        return getattr(datum, display_key, None)

    def has_prev_data(self):
        """Returns a boolean value indicating whether there is previous data.

        Returns True if there is previous data available to this table
        from the source (generally an API).

        The method is largely meant for internal use, but if you want to
        override it to provide custom behavior you can do so at your own risk.
        """
        return self._meta.has_prev_data

    def has_more_data(self):
        """Returns a boolean value indicating whether there is more data.

        Returns True if there is more data available to this table
        from the source (generally an API).

        The method is largely meant for internal use, but if you want to
        override it to provide custom behavior you can do so at your own risk.
        """
        return self._meta.has_more_data

    def get_prev_marker(self):
        """Returns the identifier for the first object in the current data set.

        The return value will be used as marker/limit-based paging in the API.
        """
        return http.urlquote_plus(self.get_object_id(self.data[0])) \
            if self.data else ''

    def get_marker(self):
        """Returns the identifier for the last object in the current data set.

        The return value will be used as marker/limit-based paging in the API.
        """
        return http.urlquote_plus(self.get_object_id(self.data[-1])) \
            if self.data else ''

    def get_prev_pagination_string(self):
        """Returns the query parameter string to paginate to the prev page."""
        return "=".join([self._meta.prev_pagination_param,
                         self.get_prev_marker()])

    def get_pagination_string(self):
        """Returns the query parameter string to paginate to the next page."""
        return "=".join([self._meta.pagination_param, self.get_marker()])

    def calculate_row_status(self, statuses):
        """Returns a boolean value determining the overall row status.

        It is detremined based on the dictionary of column name
        to status mappings passed in.

        By default, it uses the following logic:

        #. If any statuses are ``False``, return ``False``.
        #. If no statuses are ``False`` but any or ``None``, return ``None``.
        #. If all statuses are ``True``, return ``True``.

        This provides the greatest protection against false positives without
        weighting any particular columns.

        The ``statuses`` parameter is passed in as a dictionary mapping
        column names to their statuses in order to allow this function to
        be overridden in such a way as to weight one column's status over
        another should that behavior be desired.
        """
        values = statuses.values()
        if any([status is False for status in values]):
            return False
        elif any([status is None for status in values]):
            return None
        else:
            return True

    def get_row_status_class(self, status):
        """Returns a css class name determined by the status value.

        This class name is used to indicate the status of the rows in the table
        if any ``status_columns`` have been specified.
        """
        if status is True:
            return "status_up"
        elif status is False:
            return "status_down"
        else:
            return "warning"

    def get_columns(self):
        """Returns this table's columns including auto-generated ones."""
        return self.columns.values()

    def get_rows(self):
        """Return the row data for this table broken out by columns."""
        rows = []
        try:
            for datum in self.filtered_data:
                row = self._meta.row_class(self, datum)
                if self.get_object_id(datum) == self.current_item_id:
                    self.selected = True
                    row.classes.append('current_selected')
                rows.append(row)
        except Exception:
            # Exceptions can be swallowed at the template level here,
            # re-raising as a TemplateSyntaxError makes them visible.
            LOG.exception("Error while rendering table rows.")
            exc_info = sys.exc_info()
            raise six.reraise(template.TemplateSyntaxError, exc_info[1],
                              exc_info[2])

        return rows

    def css_classes(self):
        """Returns the additional CSS class to be added to <table> tag."""
        return self._meta.css_classes
