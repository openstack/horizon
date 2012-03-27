======================
The ``horizon`` Module
======================

.. module:: horizon

Horizon ships with a single point of contact for hooking into your project if
you aren't developing your own :class:`~horizon.Dashboard` or
:class:`~horizon.Panel`::

    import horizon

From there you can access all the key methods you need.

Horizon
=======

.. attribute:: urls

    The auto-generated URLconf for Horizon. Usage::

        url(r'', include(horizon.urls)),

.. autofunction:: register
.. autofunction:: unregister
.. autofunction:: get_absolute_url
.. autofunction:: get_user_home
.. autofunction:: get_dashboard
.. autofunction:: get_default_dashboard
.. autofunction:: get_dashboards

Dashboard
=========

.. autoclass:: Dashboard
    :members:

Panel
=====

.. autoclass:: Panel
    :members:

.. autoclass:: PanelGroup
    :members:
