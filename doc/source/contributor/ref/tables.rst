.. _ref-datatables:

==================
Horizon DataTables
==================

.. module:: horizon.tables

Horizon includes a componentized API for programmatically creating tables
in the UI. Why would you want this? It means that every table renders
correctly and consistently, table-level and row-level actions all have a
consistent API and appearance, and generally you don't have to reinvent the
wheel or copy-and-paste every time you need a new table!

.. seealso::

   For usage information, tips & tricks and more examples check out
   the :ref:`topics-datatables`.

DataTable
=========

The core class which defines the high-level structure of the table being
represented. Example::

    class MyTable(DataTable):
        name = Column('name')
        email = Column('email')

        class Meta(object):
            name = "my_table"
            table_actions = (MyAction, MyOtherAction)
            row_actions = (MyAction)

A full reference is included below:

.. autoclass:: DataTable
    :members:

DataTable Options
=================

The following options can be defined in a ``Meta`` class inside a
:class:`.DataTable` class. Example::

    class MyTable(DataTable):
        class Meta(object):
            name = "my_table"
            verbose_name = "My Table"

.. autoclass:: horizon.tables.base.DataTableOptions
    :members:

FormsetDataTable
================

You can integrate the :class:`.DataTable` with a Django Formset using one of
following classes:

.. autoclass:: horizon.tables.formset.FormsetDataTableMixin
    :members:

.. autoclass:: horizon.tables.formset.FormsetDataTable
    :members:

Table Components
================

.. autoclass:: Column
    :members:

.. autoclass:: Row
    :members:

Actions
=======

.. autoclass:: Action
    :members:

.. autoclass:: LinkAction
    :members:

.. autoclass:: FilterAction
    :members:

.. autoclass:: FixedFilterAction
    :members:

.. autoclass:: BatchAction
    :members:

.. autoclass:: DeleteAction
    :members:

Class-Based Views
=================

Several class-based views are provided to make working with DataTables
easier in your UI.

.. autoclass:: DataTableView

.. autoclass:: MultiTableView

Additional Features
===================
Compound sorting
----------------

In the Horizon dashboard, most tables that
display lists of resources (such as instances, volumes,
images, etc.) support sorting by clicking on the column headers.

To enable compound sorting, you can hold down the Shift key while
clicking on additional column headers. This allows you to sort
the table by multiple columns in the order you click them.

An up or down arrow indicator shows next to the column headers
you chose to sort by.
