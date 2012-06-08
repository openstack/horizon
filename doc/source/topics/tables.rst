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
to display your table with just a couple lines of code. At it's simplest it
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
of the standard ``Action`` class.

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
