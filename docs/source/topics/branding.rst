==============================
Change the branding of Horizon
==============================

Changing the Page Title
=======================

The OpenStack Dashboard Page Title branding (i.e. "**OpenStack** Dashboard")
can be overwritten by adding the attribute ``SITE_BRANDING``
to ``local_settings.py`` with the value being the desired name.

The file ``local_settings.py`` can be found at the Horizon directory path of
``horizon/openstack-dashboard/local/local_settings.py``.

Changing the Page Logo
=======================

The OpenStack Logo is pulled in through ``style.css``::

    #splash .modal {
        background: #fff url(../images/logo.png) no-repeat center 35px;

    h1.brand a {
        background: url(../images/logo.png) top left no-repeat;

To override the OpenStack Logo image, replace the image at the directory path
``horizon/openstack-dashboard/dashboard/static/dashboard/images/logo.png``.

The dimensions should be ``width: 108px, height: 121px``.
