===================
Customizing Horizon
===================

Changing the Site Title
=======================

The OpenStack Dashboard Site Title branding (i.e. "**OpenStack** Dashboard")
can be overwritten by adding the attribute ``SITE_BRANDING``
to ``local_settings.py`` with the value being the desired name.

The file ``local_settings.py`` can be found at the Horizon directory path of
``horizon/openstack-dashboard/local/local_settings.py``.

Changing the Logo
=================

The OpenStack Logo is pulled in through ``style.css``::

    #splash .modal {
        background: #fff url(../images/logo.png) no-repeat center 35px;

    h1.brand a {
        background: url(../images/logo.png) top left no-repeat;

To override the OpenStack Logo image, replace the image at the directory path
``horizon/openstack-dashboard/dashboard/static/dashboard/images/logo.png``.

The dimensions should be ``width: 108px, height: 121px``.

Modifying Existing Dashboards and Panels
========================================

If you wish to alter dashboards or panels which are not part of your codebase,
you can specify a custom python module which will be loaded after the entire
Horizon site has been initialized, but prior to the URLconf construction.
This allows for common site-customization requirements such as:

* Registering or unregistering panels from an existing dashboard.
* Changing the names of dashboards and panels.
* Re-ordering panels within a dashboard or panel group.

To specify the python module containing your modifications, add the key
``customization_module`` to your ``settings.HORIZON_CONFIG`` dictionary.
The value should be a string containing the path to your module in dotted
python path notation. Example::

    HORIZON_CONFIG = {
        "customization_module": "my_project.overrides"
    }

You can do essentially anything you like in the customization module. For
example, you could change the name of a panel::

    from django.utils.translation import ugettext_lazy as _

    import horizon

    # Rename "User Settings" to "User Options"
    settings = horizon.get_dashboard("settings")
    user_panel = settings.get_panel("user")
    user_panel.name = _("User Options")

Or get the instances panel::

    projects_dashboard = horizon.get_dashboard("project")
    instances_panel = projects_dashboard.get_panel("instances")

And limit access to users with the Keystone Admin role::

    permissions = list(getattr(instances_panel, 'permissions', []))
    permissions.append('openstack.roles.admin')
    instances_panel.permissions = tuple(permissions)

Or just remove it entirely::

    projects_dashboard.unregister(instances_panel.__class__)

.. NOTE::

    ``my_project.overrides`` needs to be importable by the python process running
    Horizon.
    If your module is not installed as a system-wide python package,
    you can either make it installable (e.g., with a setup.py)
    or you can adjust the python path used by your WSGI server to include its location.

    Probably the easiest way is to add a ``python-path`` argument to
    the ``WSGIDaemonProcess`` line in Apache's Horizon config.

    Assuming your ``my_project`` module lives in ``/opt/python/my_project``,
    you'd make it look like the following::

        WSGIDaemonProcess [... existing options ...] python-path=/opt/python


Button Icons
============

Horizon provides hooks for customizing the look and feel of each class of
button on the site. The following classes are used to identify each type of
button:

* Generic Classes
    * btn-search
    * btn-delete
    * btn-upload
    * btn-download
    * btn-create
    * btn-edit
    * btn-list
    * btn-copy
    * btn-camera
    * btn-stats
    * btn-enable
    * btn-disable

* Floating IP-specific Classes
    * btn-allocate
    * btn-release
    * btn-associate
    * btn-disassociate

* Instance-specific Classes
    * btn-launch
    * btn-terminate
    * btn-reboot
    * btn-pause
    * btn-suspend
    * btn-console
    * btn-log

* Volume-specific classes
    * btn-detach

Additionally, the site-wide default button classes can be configured by
setting ``ACTION_CSS_CLASSES`` to a tuple of the classes you wish to appear
on all action buttons in your ``local_settings.py`` file.
