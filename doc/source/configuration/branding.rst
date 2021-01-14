================
Branding Horizon
================

As of the Liberty release, Horizon has begun to conform more strictly to
Bootstrap standards in an effort to embrace more responsive web design as well
as alleviate the future need to re-brand new functionality for every release.

Supported Components
--------------------
The following components, organized by release, are the only ones that make
full use of the Bootstrap theme architecture.

* 8.0.0 (Liberty)

  * `Top Navbar`_
  * `Side Nav`_
  * `Pie Charts`_

* 9.0.0 (Mitaka)

  * Tables_
  * `Bar Charts`_
  * Login_
  * Tabs_
  * Alerts_
  * Checkboxes_

Step 1
------

The first step needed to create a custom branded theme for Horizon is to create
a custom Bootstrap theme.  There are several tools to aid in this. Some of the
more useful ones include:

- `Bootswatchr`_
- `Paintstrap`_
- `Bootstrap`_

.. note::

    Bootstrap uses LESS by default, but we use SCSS.  All of the above
    tools will provide the ``variables.less`` file, which will need to be
    converted to ``_variables.scss``

Top Navbar
----------

The top navbar in Horizon now uses a native Bootstrap ``navbar``.  There are a
number of variables that can be used to customize this element.  Please see the
**Navbar** section of your variables file for specifics on what can be set: any
variables that use ``navbar-default``.

It is important to also note that the navbar now uses native Bootstrap
dropdowns, which are customizable with variables.  Please see the **Dropdowns**
section of your variables file.

The top navbar is now responsive on smaller screens.  When the window size hits
your ``$screen-sm`` value, the topbar will compress into a design that is
better suited for small screens.

Side Nav
--------

The side navigation component has been refactored to use the native Stacked
Pills element from Bootstrap.  See **Pills** section of your variables file
for specific variables to customize.

Charts
------

Pie Charts
~~~~~~~~~~

Pie Charts are SVG elements.  SVG elements allow CSS customizations for
only a basic element's look and feel (i.e. colors, size).

Since there is no native element in Bootstrap specifically for pie charts,
the look and feel of the charts are inheriting from other elements of the
theme. Please see ``_pie_charts.scss`` for specifics.

.. _Bar Charts:

Bar Charts
~~~~~~~~~~

Bar Charts can be either a Bootstrap Progress Bar or an SVG element. Either
implementation will use the Bootstrap Progress Bar styles.

The SVG implementation will not make use of the customized Progress Bar
height though, so it is recommended that Bootstrap Progress Bars are used
whenever possible.

Please see ``_bar_charts.scss`` for specifics on what can be customized for
SVGs.  See the **Progress bars** section of your variables file for specific
variables to customize.

Tables
------

The standard Django tables now make use of the native Bootstrap table markup.
See **Tables** section of your variables file for variables to customize.

The standard Bootstrap tables will be borderless by default.  If you wish to
add a border, like the ``default`` theme, see
``openstack_dashboard/themes/default/horizon/components/_tables.scss``

.. _Login:

Login
-----

Login Splash Page
~~~~~~~~~~~~~~~~~

The login splash page now uses a standard Bootstrap panel in its
implementation. See the **Panels** section in your variables file to variables
to easily customize.

Modal Login
~~~~~~~~~~~

The modal login experience, as used when switching regions, uses a standard
Bootstrap dialog.  See the **Modals** section of your variables file for
specific variables to customize.

Tabs
----

The standard tabs make use of the native Bootstrap tab markup.

See **Tabs** section of your variables file for variables to customize.

Alerts
------

Alerts use the basic Bootstrap brand colors.  See **Colors** section of your
variables file for specifics.

Checkboxes
----------

Horizon uses icon fonts to represent checkboxes.  In order to customize
this, you simply need to override the standard scss.  For an example of
this, see themes/material/static/horizon/components/_checkboxes.scss

Bootswatch and Material Design
------------------------------

`Bootswatch`_ is a collection of free themes for Bootstrap and is now
available for use in Horizon.

In order to showcase what can be done to enhance an existing Bootstrap theme,
Horizon now includes a secondary theme, roughly based on `Google's Material
Design`_ called ``material``.  Bootswatch's **Paper** is a simple Bootstrap
implementation of Material Design and is used by ``material``.

Bootswatch provides a number of other themes, that once Horizon is fully theme
compliant, will allow easy toggling and customizations for darker or
accessibility driven experiences.

Development Tips
----------------

When developing a new theme for Horizon, it is required that the dynamically
generated `static` directory be cleared after each change and the server
restarted.  This is not always ideal.  If you wish to develop and not have
to restart the server each time, it is recommended that you configure your
development environment to not run in OFFLINE mode.  Simply verify the
following settings in your local_settings.py::

  COMPRESS_OFFLINE = False
  COMPRESS_ENABLED = False

..  _Bootstrap: http://getbootstrap.com/customize/
..  _Bootswatch: http://bootswatch.com
..  _Bootswatchr: https://codepen.io/technabors/pen/eWPXEd
..  _Paintstrap: http://paintstrap.com
..  _Google's Material Design: https://www.google.com/design/spec/material-design/introduction.html
