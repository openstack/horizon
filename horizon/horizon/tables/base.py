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

import collections
import copy
import logging
from operator import attrgetter
import sys

from django import forms
from django import template
from django.conf import settings
from django.contrib import messages
from django.core import urlresolvers
from django.utils import http
from django.utils.datastructures import SortedDict
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe

from horizon import exceptions
from .actions import FilterAction, LinkAction


LOG = logging.getLogger(__name__)

STRING_SEPARATOR = "__"


class Column(object):
    """ A class which represents a single column in a :class:`.DataTable`.

    .. attribute:: transform

        A string or callable. If ``transform`` is a string, it should be the
        name of the attribute on the underlying data class which
        should be displayed in this column. If it is a callable, it
        will be passed the current row's data at render-time and should
        return the contents of the cell. Required.

    .. attribute:: verbose_name

        The name for this column which should be used for display purposes.
        Defaults to the value of ``transform`` with the first letter
        of each word capitalized.

    .. attribute:: sortable

        Boolean to determine whether this column should be sortable or not.
        Defaults to False.

    .. attribute:: hidden

        Boolean to determine whether or not this column should be displayed
        when rendering the table. Default: ``False``.

    .. attribute:: link

        A string or callable which returns a URL which will be wrapped around
        this column's text as a link.

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
                    ('true', True)
                    ('up', True),
                    ('active', True),
                    ('on', True),
                    ('none', None),
                    ('unknown', None),
                    ('', None),
                    ('disabled', False),
                    ('down', False),
                    ('false', False),
                    ('inactive', False),
                    ('off', False),
                )

    .. attribute:: empty_value

        A string to be used for cells which have no data. Defaults to an
        empty string.

    .. attribute:: filters

        A list of functions (often template filters) to be applied to the
        value of the data for this column prior to output. This is effectively
        a shortcut for writing a custom ``transform`` function in simple cases.
    """
    # Used to retain order when instantiating columns on a table
    creation_counter = 0
    # Used for special auto-generated columns
    auto = None

    transform = None
    name = None
    verbose_name = None
    status_choices = (
        ('enabled', True),
        ('true', True),
        ('up', True),
        ('active', True),
        ('on', True),
        ('none', None),
        ('unknown', None),
        ('', None),
        ('disabled', False),
        ('down', False),
        ('false', False),
        ('inactive', False),
        ('off', False),
    )

    def __init__(self, transform, verbose_name=None, sortable=False,
                 link=None, hidden=False, attrs=None, status=False,
                 status_choices=None, empty_value=None, filters=None):
        if callable(transform):
            self.transform = transform
            self.name = transform.__name__
        else:
            self.transform = unicode(transform)
            self.name = self.transform
        self.sortable = sortable
        # Empty string is a valid value for verbose_name
        if verbose_name is None:
            verbose_name = self.transform.title()
        else:
            verbose_name = verbose_name
        self.verbose_name = unicode(verbose_name)
        self.link = link
        self.hidden = hidden
        self.status = status
        self.empty_value = empty_value or ''
        self.filters = filters or []
        if status_choices:
            self.status_choices = status_choices

        self.creation_counter = Column.creation_counter
        Column.creation_counter += 1

        self.attrs = {"classes": []}
        self.attrs.update(attrs or {})
        # Make sure we have a mutable list.
        self.attrs['classes'] = list(self.attrs['classes'])
        if self.sortable:
            self.attrs['classes'].append("sortable")
        if self.hidden:
            self.attrs['classes'].append("hide")

    def __unicode__(self):
        return self.verbose_name

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.name)

    def get_data(self, datum):
        """
        Returns the appropriate data for this column from the given input.

        The return value will be either the attribute specified for this column
        or the return value of the attr:`~horizon.tables.Column.transform`
        method for this column.
        """
        datum_id = self.table.get_object_id(datum)
        if datum_id in self.table._data_cache[self]:
            return self.table._data_cache[self][datum_id]

        # Callable transformations
        if callable(self.transform):
            data = self.transform(datum)
        # Basic object lookups
        elif hasattr(datum, self.transform):
            data = getattr(datum, self.transform, None)
        # Dict lookups
        elif isinstance(datum, collections.Iterable) and \
                self.transform in datum:
            data = datum.get(self.transform)
        else:
            if settings.DEBUG:
                messages.error(self.table._meta.request,
                               _("The attribute %(attr)s doesn't exist on "
                                 "%(obj)s.") % {'attr': self.transform,
                                                'obj': datum})
            data = None
        for filter_func in self.filters:
            data = filter_func(data)
        self.table._data_cache[self][datum_id] = data
        return self.table._data_cache[self][datum_id]

    def get_classes(self):
        """ Returns a flattened string of the column's CSS classes. """
        return " ".join(self.attrs['classes'])

    def get_link_url(self, datum):
        """ Returns the final value for the column's ``link`` property.

        If ``link`` is a callable, it will be passed the current data object
        and should return a URL. Otherwise ``get_link_url`` will attempt to
        call ``reverse`` on ``link`` with the object's id as a parameter.
        Failing that, it will simply return the value of ``link``.
        """
        obj_id = self.table.get_object_id(datum)
        if callable(self.link):
            return self.link(datum)
        try:
            return urlresolvers.reverse(self.link, args=(obj_id,))
        except urlresolvers.NoReverseMatch:
            return self.link


class Row(object):
    """ Represents a row in the table.

    When iterated, the ``Row`` instance will yield each of its cells.

    .. attribute:: table

        The table which this row belongs to.

    .. attribute:: datum

        The data object which this row represents.

    .. attribute:: id

        A string uniquely representing this row composed of the table name
        and the row data object's identifier.

    .. attribute:: cells

        The cells belonging to this row stored in a ``SortedDict`` object.
        This attribute is populated during instantiation.

    .. attribute:: status

        Boolean value representing the status of this row according
        to the value of the table's ``status_column`` value if it is set.

    .. attribute:: status_class

        Returns a css class for the status of the row based on ``status``.
    """
    def __init__(self, table, datum):
        self.table = table
        self.datum = datum
        id_vals = {"table": self.table.name,
                   "sep": STRING_SEPARATOR,
                   "id": table.get_object_id(datum)}
        self.id = "%(table)s%(sep)srow%(sep)s%(id)s" % id_vals

        # Compile all the cells on instantiation
        cells = []
        for column in table.columns.values():
            if column.auto == "multi_select":
                widget = forms.CheckboxInput(check_test=False)
                # Convert value to string to avoid accidental type conversion
                data = widget.render('object_ids',
                                     str(table.get_object_id(datum)))
                table._data_cache[column][table.get_object_id(datum)] = data
            elif column.auto == "actions":
                data = table.render_row_actions(datum)
                table._data_cache[column][table.get_object_id(datum)] = data
            else:
                data = column.get_data(datum)
            cell = Cell(datum, data, column, self)
            cells.append((column.name or column.auto, cell))
        self.cells = SortedDict(cells)

    @property
    def status(self):
        column_name = self.table._meta.status_column
        if column_name:
            return self.cells[column_name].status

    @property
    def status_class(self):
        column_name = self.table._meta.status_column
        if column_name:
            return self.cells[column_name].get_status_class(self.status)
        else:
            return ''

    def get_cells(self):
        """ Returns the bound cells for this row in order. """
        return self.cells.values()

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.id)

    def __iter__(self):
        return iter(self.cells.values())


class Cell(object):
    """ Represents a single cell in the table. """
    def __init__(self, datum, data, column, row, attrs=None):
        self.datum = datum
        self.data = data
        self.column = column
        self.row = row
        self.attrs = {'classes': []}
        self.attrs.update(attrs or {})

    def __repr__(self):
        return '<%s: %s, %s>' % (self.__class__.__name__,
                                 self.column.name,
                                 self.row.id)

    @property
    def value(self):
        """
        Returns a formatted version of the data for final output.

        This takes into consideration the
        :attr:`~horizon.tables.Column.link`` and
        :attr:`~horizon.tables.Column.empty_value`
        attributes.
        """
        try:
            data = self.column.get_data(self.datum) or self.column.empty_value
        except Exception as ex:
            data = None
            exc_info = sys.exc_info()
            raise template.TemplateSyntaxError, exc_info[1], exc_info[2]
        if self.column.link:
            url = self.column.get_link_url(self.datum)
            # Escape the data inside while allowing our HTML to render
            data = mark_safe('<a href="%s">%s</a>' % (url, escape(data)))
        return data

    @property
    def status(self):
        """ Gets the status for the column based on the cell's data. """
        # Deal with status column mechanics based in this cell's data
        if hasattr(self, '_status'):
            return self._status
        self._status = None
        if self.column.status or \
                self.column.table._meta.status_column == self.column.name:
            status_matches = [status[1] for status in
                              self.column.status_choices if
                              str(self.data).lower() == status[0]]
            try:
                self._status = status_matches[0]
            except IndexError:
                LOG.exception('The value "%s" of the data in the status '
                              'column didn\'t match any value in '
                              'status_choices' % str(self.data).lower())
        return self._status

    def get_status_class(self, status):
        """ Returns a css class name determined by the status value. """
        if status is True:
            return "status_up"
        elif status is False:
            return "status_down"
        else:
            return "status_unknown"

    def get_classes(self):
        """ Returns a flattened string of the cell's CSS classes. """
        union = set(self.attrs['classes']) | set(self.column.attrs['classes'])
        if self.column.status:
            union.add(self.get_status_class(self.status))
        return " ".join(union)


class DataTableOptions(object):
    """ Contains options for :class:`.DataTable` objects.

    .. attribute:: name

        A short name or slug for the table.

    .. attribute:: verbose_name

        A more verbose name for the table meant for display purposes.

    .. attribute:: columns

        A list of column objects or column names. Controls ordering/display
        of the columns in the table.

    .. attribute:: table_actions

        A list of action classes derived from the :class:`.Action` class.
        These actions will handle tasks such as bulk deletion, etc. for
        multiple objects at once.

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
        of :class:`.FilterAction` is in :attr:`.table_actions`.

    .. attribute:: template

        String containing the template which should be used to render the
        table. Defaults to ``"horizon/common/_data_table.html"``.

    .. attribute:: context_var_name

        The name of the context variable which will contain the table when
        it is rendered. Defaults to ``"table"``.

    .. attribute:: status_column

        The name of a column on this table which represents the "state"
        of the data object being represented. The collumn must already be
        designated as a status column by passing the ``status=True``
        parameter to the column.

        If ``status_column`` is set, when the rows are rendered the value
        of this column will be used to add an extra class to the row in
        the form of ``"status_up"`` or ``"status_down"`` for that row's
        data.

        This is useful for displaying the enabled/disabled status of a
        service, for example.
    """
    def __init__(self, options):
        self.name = getattr(options, 'name', self.__class__.__name__)
        verbose_name = getattr(options, 'verbose_name', None) \
                                    or self.name.title()
        self.verbose_name = unicode(verbose_name)
        self.columns = getattr(options, 'columns', None)
        self.status_column = getattr(options, 'status_column', None)
        self.table_actions = getattr(options, 'table_actions', [])
        self.row_actions = getattr(options, 'row_actions', [])

        # Set self.filter if we have any FilterActions
        filter_actions = [action for action in self.table_actions if
                          issubclass(action, FilterAction)]
        if len(filter_actions) > 1:
            raise NotImplementedError("Multiple filter actions is not "
                                      "currently supported.")
        self.filter = getattr(options, 'filter', len(filter_actions) > 0)
        if len(filter_actions) == 1:
            self._filter_action = filter_actions.pop()
        else:
            self._filter_action = None

        self.template = 'horizon/common/_data_table.html'
        self.row_actions_template = \
                        'horizon/common/_data_table_row_actions.html'
        self.table_actions_template = \
                        'horizon/common/_data_table_table_actions.html'
        self.context_var_name = unicode(getattr(options,
                                                'context_var_nam',
                                                'table'))
        self.actions_column = getattr(options,
                                     'actions_column',
                                     len(self.row_actions) > 0)
        self.multi_select = getattr(options,
                                    'multi_select',
                                    len(self.table_actions) > 0)

        # Set runtime table defaults; not configurable.
        self.has_more_data = False


class DataTableMetaclass(type):
    """ Metaclass to add options to DataTable class and collect columns. """
    def __new__(mcs, name, bases, attrs):
        # Process options from Meta
        attrs["_meta"] = opts = DataTableOptions(attrs.get("Meta", None))

        # Gather columns; this prevents the column from being an attribute
        # on the DataTable class and avoids naming conflicts.
        columns = [(column_name, attrs.pop(column_name)) for \
                            column_name, obj in attrs.items() \
                            if isinstance(obj, Column)]
        # add a name attribute to each column
        for column_name, column in columns:
            column.name = column_name
        columns.sort(key=lambda x: x[1].creation_counter)
        # Iterate in reverse to preserve final order
        for base in bases[::-1]:
            if hasattr(base, 'base_columns'):
                columns = base.base_columns.items() + columns
        attrs['base_columns'] = SortedDict(columns)

        if opts.columns:
            # Remove any columns that weren't declared if we're being explicit
            # NOTE: we're iterating a COPY of the list here!
            for column_data in columns[:]:
                if column_data[0] not in opts.columns:
                    columns.pop(columns.index(column_data))
            # Re-order based on declared columns
            columns.sort(key=lambda x: attrs['_meta'].columns.index(x[0]))
        # Add in our auto-generated columns
        if opts.multi_select:
            multi_select = Column("multi_select",
                                  verbose_name="",
                                  attrs={'classes': ('multi_select_column',)})
            multi_select.auto = "multi_select"
            columns.insert(0, ("multi_select", multi_select))
        if opts.actions_column:
            actions_column = Column("actions",
                                    attrs={'classes': ('actions_column',)})
            actions_column.auto = "actions"
            columns.append(("actions", actions_column))
        attrs['columns'] = SortedDict(columns)

        # Gather and register actions for later access since we only want
        # to instantiate them once.
        # (list() call gives deterministic sort order, which sets don't have.)
        actions = list(set(opts.row_actions) | set(opts.table_actions))
        actions.sort(key=attrgetter('name'))
        actions_dict = SortedDict([(action.name, action()) \
                                   for action in actions])
        attrs['base_actions'] = actions_dict
        if opts._filter_action:
            # Replace our filter action with the instantiated version
            opts._filter_action = actions_dict[opts._filter_action.name]

        # Create our new class!
        return type.__new__(mcs, name, bases, attrs)


class DataTable(object):
    """ A class which defines a table with all data and associated actions.

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
    __metaclass__ = DataTableMetaclass

    def __init__(self, request, data, **kwargs):
        self._meta.request = request
        self._meta.data = data
        self._populate_data_cache()
        self.kwargs = kwargs

        for column in self.columns.values():
            column.table = self

        # Associate these actions with this table
        for action in self.base_actions.values():
            action.table = self
        if self._meta._filter_action:
            param_name = self._meta._filter_action.get_param_name()
            q = self._meta.request.POST.get(param_name, '')
            self._meta._filter_action.filter_string = q

    def __unicode__(self):
        return self._meta.verbose_name

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.name)

    @property
    def name(self):
        return self._meta.name

    @property
    def data(self):
        return self._meta.data

    @property
    def multi_select(self):
        return self._meta.multi_select

    @property
    def filtered_data(self):
        if not hasattr(self, '_filtered_data'):
            self._filtered_data = self.data
            if self._meta.filter and self._meta._filter_action:
                action = self._meta._filter_action
                self._filtered_data = action.filter(self,
                                                    self.data,
                                                    action.filter_string)
        return self._filtered_data

    def _populate_data_cache(self):
        self._data_cache = {}
        # Set up hash tables to store data points for each column
        for column in self.get_columns():
            self._data_cache[column] = {}

    def _filter_action(self, action, request, datum=None):
        try:
            # Catch user errors in permission functions here
            return action.allowed(request, datum)
        except Exception:
            LOG.exception("Error while checking action permissions.")
            return None

    def render(self):
        """ Renders the table using the template from the table options. """
        table_template = template.loader.get_template(self._meta.template)
        extra_context = {self._meta.context_var_name: self}
        context = template.RequestContext(self._meta.request, extra_context)
        return table_template.render(context)

    def get_absolute_url(self):
        """ Returns the canonical URL for this table.

        This is used for the POST action attribute on the form element
        wrapping the table. In many cases it is also useful for redirecting
        after a successful action on the table.

        For convenience it defaults to the value of
        ``request.get_full_path()``, e.g. the path at which the table
        was requested.
        """
        return self._meta.request.get_full_path()

    def get_empty_message(self):
        """ Returns the message to be displayed when there is no data. """
        return _("No items to display.")

    def get_object_by_id(self, lookup):
        """
        Returns the data object from the table's dataset which matches
        the ``lookup`` parameter specified. An error will be raised if
        the match is not a single data object.

        Uses :meth:`~horizon.tables.DataTable.get_object_id` internally.
        """
        matches = [datum for datum in self.data if
                   self.get_object_id(datum) == lookup]
        if len(matches) > 1:
            raise ValueError("Multiple matches were returned for that id: %s."
                           % matches)
        if not matches:
            raise exceptions.Http302(self.get_absolute_url(),
                                     _('No match returned for the id "%s".')
                                       % lookup)
        return matches[0]

    def get_table_actions(self):
        """ Returns a list of the action instances for this table. """
        bound_actions = [self.base_actions[action.name] for
                         action in self._meta.table_actions]
        return [action for action in bound_actions if
                self._filter_action(action, self._meta.request)]

    def get_row_actions(self, datum):
        """ Returns a list of the action instances for a specific row. """
        bound_actions = []
        for action in self._meta.row_actions:
            # Copy to allow modifying properties per row
            bound_action = copy.copy(self.base_actions[action.name])
            # Remove disallowed actions.
            if not self._filter_action(bound_action,
                                       self._meta.request,
                                       datum):
                continue
            # Hook for modifying actions based on data. No-op by default.
            bound_action.update(self._meta.request, datum)
            # Pre-create the URL for this link with appropriate parameters
            if isinstance(bound_action, LinkAction):
                bound_action.bound_url = bound_action.get_link_url(datum)
            bound_actions.append(bound_action)
        return bound_actions

    def render_table_actions(self):
        """ Renders the actions specified in ``Meta.table_actions``. """
        template_path = self._meta.table_actions_template
        table_actions_template = template.loader.get_template(template_path)
        bound_actions = self.get_table_actions()
        extra_context = {"table_actions": bound_actions}
        if self._meta.filter:
            extra_context["filter"] = self._meta._filter_action
        context = template.RequestContext(self._meta.request, extra_context)
        return table_actions_template.render(context)

    def render_row_actions(self, datum):
        """
        Renders the actions specified in ``Meta.row_actions`` using the
        current row data. """
        template_path = self._meta.row_actions_template
        row_actions_template = template.loader.get_template(template_path)
        bound_actions = self.get_row_actions(datum)
        extra_context = {"row_actions": bound_actions,
                         "row_id": self.get_object_id(datum)}
        context = template.RequestContext(self._meta.request, extra_context)
        return row_actions_template.render(context)

    def parse_action(self, action_string):
        """
        Parses the ``action`` parameter (a string) sent back with the
        POST data. By default this parses a string formatted as
        ``{{ table_name }}__{{ action_name }}__{{ row_id }}`` and returns
        each of the pieces. The ``row_id`` is optional.
        """
        if action_string:
            bits = action_string.split(STRING_SEPARATOR)
            bits.reverse()
            table = bits.pop()
            action = bits.pop()
            try:
                object_id = bits.pop()
            except IndexError:
                object_id = None
            return table, action, object_id

    def take_action(self, action_name, obj_id=None, obj_ids=None):
        """
        Locates the appropriate action and routes the object
        data to it. The action should return an HTTP redirect
        if successful, or a value which evaluates to ``False``
        if unsuccessful.
        """
        # See if we have a list of ids
        obj_ids = obj_ids or self._meta.request.POST.getlist('object_ids')
        action = self.base_actions.get(action_name, None)
        if action and (not action.requires_input or obj_id or obj_ids):
            if obj_id:
                obj_id = self.sanitize_id(obj_id)
            if obj_ids:
                obj_ids = [self.sanitize_id(i) for i in obj_ids]
            # Single handling is easy
            if not action.handles_multiple:
                response = action.single(self, self._meta.request, obj_id)
            # Otherwise figure out what to pass along
            else:
                if obj_id and not obj_ids:
                    obj_ids = [obj_id]
                response = action.multiple(self, self._meta.request, obj_ids)
            return response
        elif action and action.requires_input and not (obj_id or obj_ids):
            messages.info(self._meta.request,
                          _("Please select a row before taking that action."))
        return None

    def maybe_handle(self):
        """ Determine whether the request should be handled by this table. """
        request = self._meta.request
        if request.method == "POST":
            action_string = request.POST.get('action', None)
            if action_string:
                table_id, action, obj_id = self.parse_action(action_string)
                if table_id == self.name and action:
                    return self.take_action(action, obj_id)
        return None

    def sanitize_id(self, obj_id):
        """ Override to modify an incoming obj_id to match existing
        API data types or modify the format.
        """
        return obj_id

    def get_object_id(self, datum):
        """ Returns the identifier for the object this row will represent.

        By default this returns an ``id`` attribute on the given object,
        but this can be overridden to return other values.
        """
        return datum.id

    def get_object_display(self, datum):
        """ Returns a display name that identifies this object.

        By default, this returns a ``name`` attribute from the given object,
        but this can be overriden to return other values.
        """
        return datum.name

    def has_more_data(self):
        """
        Returns a boolean value indicating whether there is more data
        available to this table from the source (generally an API).

        The method is largely meant for internal use, but if you want to
        override it to provide custom behavior you can do so at your own risk.
        """
        return self._meta.has_more_data

    def get_marker(self):
        """
        Returns the identifier for the last object in the current data set
        for APIs that use marker/limit-based paging.
        """
        return http.urlquote_plus(self.get_object_id(self.data[-1]))

    def get_columns(self):
        """ Returns this table's columns including auto-generated ones."""
        return self.columns.values()

    def get_rows(self):
        """ Return the row data for this table broken out by columns. """
        rows = []
        try:
            for datum in self.filtered_data:
                rows.append(Row(self, datum))
        except Exception, e:
            # Exceptions can be swallowed at the template level here,
            # re-raising as a TemplateSyntaxError makes them visible.
            LOG.exception("Error while rendering table rows.")
            exc_info = sys.exc_info()
            raise template.TemplateSyntaxError, exc_info[1], exc_info[2]
        return rows
