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

    # Rename "OpenStack Credentials" to "OS Credentials"
    settings = horizon.get_dashboard("settings")
    project_panel = settings.get_panel("project")
    project_panel.name = _("OS Credentials")

Other common options might include removing default panels, adding or
changing permissions on panels and dashboards, etc.

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
