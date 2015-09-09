======================
DataTables Topic Guide
======================

Horizon provides the :mod:`horizon.tables` module to provide
a convenient, reusable API for building data-driven displays and interfaces.
The core components of this API fall into three categories: ``DataTables``,
``Actions``, and ``Class-based Views``.

  .. seealso::

    For a detailed API information check out the :doc:`DataTables Reference
    Guide </ref/tables>`.

Tables
======

The majority of interface in a dashboard-style interface ends up being
tabular displays of the various resources the dashboard interacts with.
The :class:`~horizon.tables.DataTable` class exists so you don't have to
reinvent the wheel each time.

Creating your own tables
------------------------

Creating a table is fairly simple:

  #. Create a subclass of :class:`~horizon.tables.DataTable`.
  #. Define columns on it using :class:`~horizon.tables.Column`.
  #. Create an inner ``Meta`` class to contain the special options for
     this table.
  #. Define any actions for the table, and add them to
     :attr:`~horizon.tables.DataTableOptions.table_actions` or
     :attr:`~horizon.tables.DataTableOptions.row_actions`.

Examples of this can be found in any of the ``tables.py`` modules included
in the reference modules under ``horizon.dashboards``.

Connecting a table to a view
----------------------------

Once you've got your table set up the way you like it, the next step is to
wire it up to a view. To make this as easy as possible Horizon provides the
:class:`~horizon.tables.DataTableView` class-based view which can be subclassed
to display your table with just a couple lines of code. At its simplest, it
looks like this::

    from horizon import tables
    from .tables import MyTable


    class MyTableView(tables.DataTableView):
        table_class = MyTable
        template_name = "my_app/my_table_view.html"

        def get_data(self):
            return my_api.objects.list()

In the template you would just need to include the following to render the
table::

    {{ table.render }}

That's it! Easy, right?

Actions
=======

Actions comprise any manipulations that might happen on the data in the table
or the table itself. For example, this may be the standard object CRUD, linking
to related views based on the object's id, filtering the data in the table,
or fetching updated data when appropriate.

When actions get run
--------------------

There are two points in the request-response cycle in which actions can
take place; prior to data being loaded into the table, and after the data
is loaded. When you're using one of the pre-built class-based views for
working with your tables the pseudo-workflow looks like this:

  #. The request enters view.
  #. The table class is instantiated without data.
  #. Any "preemptive" actions are checked to see if they should run.
  #. Data is fetched and loaded into the table.
  #. All other actions are checked to see if they should run.
  #. If none of the actions have caused an early exit from the view,
     the standard response from the view is returned (usually the
     rendered table).

The benefit of the multi-step table instantiation is that you can use
preemptive actions which don't need access to the entire collection of data
to save yourself on processing overhead, API calls, etc.

Basic actions
-------------

At their simplest, there are three types of actions: actions which act on the
data in the table, actions which link to related resources, and actions that
alter which data is displayed. These correspond to
:class:`~horizon.tables.Action`, :class:`~horizon.tables.LinkAction`, and
:class:`~horizon.tables.FilterAction`.

Writing your own actions generally starts with subclassing one of those
action classes and customizing the designated attributes and methods.

Shortcut actions
----------------

There are several common tasks for which Horizon provides pre-built shortcut
classes. These include :class:`~horizon.tables.BatchAction`, and
:class:`~horizon.tables.DeleteAction`. Each of these abstracts away nearly
all of the boilerplate associated with writing these types of actions and
provides consistent error handling, logging, and user-facing interaction.

It is worth noting that ``BatchAction`` and ``DeleteAction`` are extensions
of the standard ``Action`` class. Some ``BatchAction`` or ``DeleteAction``
classes may cause some unrecoverable results, like deleted images or
unrecoverable instances. It may be helpful to specify specific help_text to
explain the concern to the user, such as "Deleted images are not recoverable".

Preemptive actions
------------------

Action classes which have their :attr:`~horizon.tables.Action.preempt`
attribute set to ``True`` will be evaluated before any data is loaded into
the table. As such, you must be careful not to rely on any table methods that
require data, such as :meth:`~horizon.tables.DataTable.get_object_display` or
:meth:`~horizon.tables.DataTable.get_object_by_id`. The advantage of preemptive
actions is that you can avoid having to do all the processing, API calls, etc.
associated with loading data into the table for actions which don't require
access to that information.

Policy checks on actions
------------------------

The :attr:`~horizon.tables.Action.policy_rules` attribute, when set, will
validate access to the action using the policy rules specified.  The attribute
is a list of scope/rule pairs.  Where the scope is the service type defining
the rule and the rule is a rule from the corresponding service policy.json
file.  The format of :attr:`horizon.tables.Action.policy_rules` looks like::

    (("identity", "identity:get_user"),)

Multiple checks can be made for the same action by merely adding more tuples
to the list.  The policy check will use information stored in the session
about the user and the result of
:meth:`~horizon.tables.Action.get_policy_target` (which can be overridden in
the derived action class) to determine if the user
can execute the action.  If the user does not have access to the action, the
action is not added to the table.

If :attr:`~horizon.tables.Action.policy_rules` is not set, no policy checks
will be made to determine if the action should be visible and will be
displayed solely based on the result of
:meth:`~horizon.tables.Action.allowed`.

For more information on policy based Role Based Access Control see:
:doc:`Horizon Policy Enforcement (RBAC: Role Based Access Control) </topics/policy>`.

Table Cell filters (decorators)
===============================

DataTable displays lists of objects in rows and object attributes in cell.
How should we proceed, if we want to decorate some column, e.g. if we have
column ``memory`` which returns a number e.g. 1024, and we want to show
something like 1024.00 GB inside table?

Decorator pattern
-----------------

The clear anti-pattern is defining the new attributes on object like
``ram_float_format_2_gb`` or to tweak a DataTable in any way for displaying
purposes.

The cleanest way is to use ``filters``. Filters are decorators, following GOF
``Decorator pattern``. This way ``DataTable logic`` and ``displayed object
logic`` are correctly separated from ``presentation logic`` of the object
inside of the various tables. And therefore the filters are reusable in all
tables.

Filter function
---------------

Horizon DatablesTable takes a tuple of pointers to filter functions
or anonymous lambda functions. When displaying a ``Cell``, ``DataTable``
takes ``Column`` filter functions from left to right, using the returned value
of the previous function as a parameter of the following function. Then
displaying the returned value of the last filter function.

A valid filter function takes one parameter and returns the decorated value.
So e.g. these are valid filter functions ::

    # Filter function.
    def add_unit(v):
      return str(v) + " GB"

    # Or filter lambda function.
    lambda v: str(v) + " GB"

    # This is also a valid definition of course, although for the change of the
    # unit parameter, function has to be wrapped by lambda
    # (e.g. floatformat function example below).
    def add_unit(v, unit="GB"):
      return str(v) + " " + unit

Using filters in DataTable column
---------------------------------

DataTable takes tuple of filter functions, so e.g. this is valid decorating
of a value with float format and with unit ::

    ram = tables.Column(
        "ram",
        verbose_name=_('Memory'),
        filters=(lambda v: floatformat(v, 2),
                 add_unit))

It always takes tuple, so using only one filter would look like this ::

    filters=(lambda v: floatformat(v, 2),)

The decorated parameter doesn't have to be only a string or number, it can
be anything e.g. list or an object. So decorating of object, that has
attributes value and unit would look like this ::

    ram = tables.Column(
            "ram",
            verbose_name=_('Memory'),
            filters=(lambda x: getattr(x, 'value', '') +
                     " " + getattr(x, 'unit', ''),))

Available filters
-----------------

There are a load of filters, that can be used, defined in django already:
https://github.com/django/django/blob/master/django/template/defaultfilters.py

So it's enough to just import and use them, e.g. ::

    from django.template import defaultfilters as filters

    # code omitted
    filters=(filters.yesno, filters.capfirst)


    from django.template.defaultfilters import timesince
    from django.template.defaultfilters import title

    # code omitted
    filters=(parse_isotime, timesince)


Inline editing
==============

Table cells can be easily upgraded with in-line editing. With use of
django.form.Field, we are able to run validations of the field and correctly
parse the data. The updating process is fully encapsulated into table
functionality, communication with the server goes through AJAX in JSON format.
The javascript wrapper for inline editing allows each table cell that has
in-line editing available to:

  #. Refresh itself with new data from the server.
  #. Display in edit mod.
  #. Send changed data to server.
  #. Display validation errors.

There are basically 3 things that need to be defined in the table in order
to enable in-line editing.

Fetching the row data
---------------------

Defining an ``get_data`` method in a class inherited from ``tables.Row``.
This method takes care of fetching the row data. This class has to be then
defined in the table Meta class as ``row_class = UpdateRow``.

Example::

    class UpdateRow(tables.Row):
        # this method is also used for automatic update of the row
        ajax = True

        def get_data(self, request, project_id):
            # getting all data of all row cells
            project_info = api.keystone.tenant_get(request, project_id,
                                                   admin=True)
            return project_info

Updating changed cell data
--------------------------

Define an ``update_cell`` method in the class inherited from
``tables.UpdateAction``. This method takes care of saving the data of the
table cell. There can be one class for every cell thanks to the
``cell_name`` parameter. This class is then defined in tables column as
``update_action=UpdateCell``, so each column can have its own updating
method.

Example::

    class UpdateCell(tables.UpdateAction):
        def allowed(self, request, project, cell):
            # Determines whether given cell or row will be inline editable
            # for signed in user.
            return api.keystone.keystone_can_edit_project()

        def update_cell(self, request, project_id, cell_name, new_cell_value):
            # in-line update project info
            try:
                project_obj = datum
                # updating changed value by new value
                setattr(project_obj, cell_name, new_cell_value)

                # sending new attributes back to API
                api.keystone.tenant_update(
                    request,
                    project_id,
                    name=project_obj.name,
                    description=project_obj.description,
                    enabled=project_obj.enabled)

            except Conflict:
                # Validation error for naming conflict, raised when user
                # choose the existing name. We will raise a
                # ValidationError, that will be sent back to the client
                # browser and shown inside of the table cell.
                message = _("This name is already taken.")
                raise ValidationError(message)
            except:
                # Other exception of the API just goes through standard
                # channel
                exceptions.handle(request, ignore=True)
                return False
            return True

Defining a form_field for each Column that we want to be in-line edited.
------------------------------------------------------------------------

Form field should be ``django.form.Field`` instance, so we can use django
validations and parsing of the values sent by POST (in example validation
``required=True`` and correct parsing of the checkbox value from the POST
data).

Form field can be also ``django.form.Widget`` class, if we need to just
display the form widget in the table and we don't need Field functionality.

Then connecting ``UpdateRow`` and ``UpdateCell`` classes to the table.

Example::

    class TenantsTable(tables.DataTable):
        # Adding html text input for inline editing, with required validation.
        # HTML form input will have a class attribute tenant-name-input, we
        # can define here any HTML attribute we need.
        name = tables.Column('name', verbose_name=_('Name'),
                             form_field=forms.CharField(required=True),
                             form_field_attributes={'class':'tenant-name-input'},
                             update_action=UpdateCell)

        # Adding html textarea without required validation.
        description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                    verbose_name=_('Description'),
                                    form_field=forms.CharField(
                                        widget=forms.Textarea(),
                                        required=False),
                                    update_action=UpdateCell)

        # Id will not be inline edited.
        id = tables.Column('id', verbose_name=_('Project ID'))

        # Adding html checkbox, that will be shown inside of the table cell with
        # label
        enabled = tables.Column('enabled', verbose_name=_('Enabled'), status=True,
                                form_field=forms.BooleanField(
                                    label=_('Enabled'),
                                    required=False),
                                update_action=UpdateCell)

        class Meta:
            name = "tenants"
            verbose_name = _("Projects")
            # Connection to UpdateRow, so table can fetch row data based on
            # their primary key.
            row_class = UpdateRow

