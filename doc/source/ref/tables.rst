==================
Horizon DataTables
==================

.. module:: horizon.tables

Horizon includes a componentized API for programmatically creating tables
in the UI. Why would you want this? It means that every table renders
correctly and consistently, table- and row-level actions all have a consistent
API and appearance, and generally you don't have to reinvent the wheel or
copy-and-paste every time you need a new table!

  .. seealso::

    For usage information, tips & tricks and more examples check out the :doc:`DataTables Topic
    Guide </topics/tables>`.

DataTable
=========

The core class which defines the high-level structure of the table being
represented. Example::

    class MyTable(DataTable):
        name = Column('name')
        email = Column('email')

        class Meta:
            name = "my_table"
            table_actions = (MyAction, MyOtherAction)
            row_actions - (MyAction)

A full reference is included below:

.. autoclass:: DataTable
    :members:

DataTable Options
=================

The following options can be defined in a ``Meta`` class inside a
:class:`.DataTable` class. Example::

    class MyTable(DataTable):
        class Meta:
            name = "my_table"
            verbose_name = "My Table"

.. autoclass:: horizon.tables.base.DataTableOptions
    :members:

FormsetDataTable
================

You can integrate the :class:`.DataTable` with a Django Formset using one of following classes:

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

.. autoclass:: UpdateAction
    :members:

Class-Based Views
=================

Several class-based views are provided to make working with DataTables
easier in your UI.

.. autoclass:: DataTableView

.. autoclass:: MultiTableView
