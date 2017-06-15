==========================
Horizon Tabs and TabGroups
==========================

.. module:: horizon.tabs

Horizon includes a set of reusable components for programmatically
building tabbed interfaces with fancy features like dynamic AJAX loading
and nearly effortless templating and styling.

Tab Groups
==========

For any tabbed interface, your fundamental element is the tab group which
contains all your tabs. This class provides a dead-simple API for building
tab groups and encapsulates all the necessary logic behind the scenes.

.. autoclass:: TabGroup
    :members:

Tabs
====

The tab itself is the discrete unit for a tab group, representing one
view of data.

.. autoclass:: Tab
    :members:

.. autoclass:: TableTab
    :members:



TabView
=======

There is also a useful and simple generic class-based view for handling
the display of a :class:`~horizon.tabs.TabGroup` class.

.. autoclass:: TabView
    :members:

.. autoclass:: TabbedTableView
    :members:
