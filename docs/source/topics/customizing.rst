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
