===================
Customizing Horizon
===================

Themes
======

As of the Kilo release, styling for the OpenStack Dashboard can be altered
through the use of a theme. A theme is a directory containing a
``_variables.scss`` file to override the color codes used throughout the SCSS
and a ``_styles.scss`` file with additional styles to load after dashboard
styles have loaded.

As of the Mitaka release, Horizon can be configured to run with multiple
themes available at run time.  It uses a browser cookie to allow users to
toggle between the configured themes.  By default, Horizon is configured
with the two standard themes available: 'default' and 'material'.

To configure or alter the available themes, set ``AVAILABLE_THEMES`` in
``local_settings.py`` to a list of tuples, such that ``('name', 'label', 'path')``

``name``
  The key by which the theme value is stored within the cookie

``label``
  The label shown in the theme toggle under the User Menu

``path``
  The directory location for the theme. The path must be relative to the
  ``openstack_dashboard`` directory or an absolute path to an accessible
  location on the file system

To use a custom theme, set ``AVAILABLE_THEMES`` in ``local_settings.py`` to
a list of themes.  If you wish to run in a mode similar to legacy Horizon,
set ``AVAILABLE_THEMES`` with a single tuple, and the theme toggle will not
be available at all through the application to allow user configuration themes.

For example, a configuration with multiple themes::

  AVAILABLE_THEMES = [
      ('default', 'Default', 'themes/default'),
      ('material', 'Material', 'themes/material'),
  ]

A configuration with a single theme::

  AVAILABLE_THEMES = [
      ('default', 'Default', 'themes/default'),
  ]

Both the Dashboard custom variables and Bootstrap variables can be overridden.
For a full list of the Dashboard SCSS variables that can be changed, see the
variables file at ``openstack_dashboard/static/dashboard/scss/_variables.scss``.

In order to build a custom theme, both ``_variables.scss`` and ``_styles.scss``
are required and ``_variables.scss`` must provide all the default Bootstrap
variables.

Inherit from an Existing Theme
------------------------------

Custom themes must implement all of the Bootstrap variables required by
Horizon in ``_variables.scss`` and ``_styles.scss``. To make this easier, you
can inherit the variables needed in the default theme and only override those
that you need to customize. To inherit from the default theme, put this in your
theme's ``_variables.scss``::

   @import "/themes/default/variables";

Once you have made your changes you must re-generate the static files with
 ``./run_tests.py -m collectstatic``.

By default, all of the themes configured by ``AVAILABLE_THEMES`` setting are
collected by horizon during the `collectstatic` process. By default, the themes
are collected into the dynamic `static/themes` directory, but this location can
be customized via the ``local_settings.py`` variable: ``THEME_COLLECTION_DIR``

Once collected, any theme configured via ``AVAILABLE_THEMES`` is available to
inherit from by importing its variables and styles from its collection
directory.  The following is an example of inheriting from the material theme::

  @import "/themes/material/variables";
  @import "/themes/material/styles";

Bootswatch
~~~~~~~~~~

Horizon packages the Bootswatch SCSS files for use with its ``material`` theme.
Because of this, it is simple to use an existing Bootswatch theme as a base.
This is due to the fact that Bootswatch is loaded as a 3rd party static asset,
and therefore is automatically collected into the `static` directory in
`/horizon/lib/`.  The following is an example of how to inherit from Bootswatch's
``darkly`` theme::

  @import "/horizon/lib/bootswatch/darkly/variables";
  @import "/horizon/lib/bootswatch/darkly/bootswatch";


Organizing Your Theme Directory
-------------------------------

A custom theme directory can be organized differently, depending on the
level of customization that is desired, as it can include static files
as well as Django templates.  It can include special subdirectories that will
be used differently: ``static``, ``templates`` and ``img``.

The ``static`` Folder
~~~~~~~~~~~~~~~~~~~~~

If the theme folder contains a sub-folder called ``static``, then that sub
folder will be used as the **static root of the theme**.  I.e., Horizon will
look in that sub-folder for the _variables.scss and _styles.scss files.
The contents of this folder will also be served up at ``/static/custom``.

The ``templates`` Folder
~~~~~~~~~~~~~~~~~~~~~~~~

If the theme folder contains a sub-folder ``templates``, then the path
to that sub-folder will be prepended to the ``TEMPLATE_DIRS`` tuple to
allow for theme specific template customizations.

Using the ``templates`` Folder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Any Django template that is used in Horizon can be overridden through a theme.
This allows highly customized user experiences to exist within the scope of
different themes.  Any template that is overridden must adhere to the same
directory structure that the extending template expects.

For example, if you wish to customize the sidebar, Horizon expects the template
to live at ``horizon/_sidebar.html``.  You would need to duplicate that
directory structure under your templates directory, such that your override
would live at ``{ theme_path }/templates/horizon/_sidebar.html``.

The ``img`` Folder
~~~~~~~~~~~~~~~~~~

If the static root of the theme folder contains an ``img`` directory,
then all images that make use of the {% themable_asset %} templatetag
can be overridden.

These assets include logo.png, splash-logo.png and favicon.ico, however
overriding the SVG/GIF assets used by Heat within the `dashboard/img` folder
is not currently supported.

Customizing the Logo
--------------------

Simple
~~~~~~

If you wish to customize the logo that is used on the splash screen or in the
top navigation bar, then you need to create an ``img`` directory under your
theme's static root directory and place your custom ``logo.png`` or
``logo-splash.png`` within it.

If you wish to override the ``logo.png`` using the previous method, and if the
image used is larger than the height of the top navigation, then the image will be
constrained to fit within the height of nav.  You can customize the height of
the top navigation bar by customizing the SCSS variable: ``$navbar-height``.
If the image's height is smaller than the navbar height, then the image
will retain its original resolution and size, and simply be centered
vertically in the available space.

Prior to the Kilo release the images files inside of Horizon needed to be
replaced by your images files or the Horizon stylesheets needed to be altered
to point to the location of your image.

Advanced
~~~~~~~~

If you need to do more to customize the logo than simply replacing the existing
PNG, then you can also override the _brand.html through a custom theme.  To use
this technique, simply add a ``templates/header/_brand.html`` to the root of
your custom theme, and add markup directly to the file.  For an example of how
to do this, see
``openstack_dashboard/themes/material/templates/header/_brand.html``.

The splash / login panel can also be customized by adding
``templates/auth/_splash.html``.  See
``openstack_dashboard/themes/material/templates/auth/_splash.html`` for an
example.


Branding Horizon
================

As of the Liberty release, Horizon has begun to conform more strictly to
Bootstrap standards in an effort to embrace more responsive web design as well
as alleviate the future need to re-brand new functionality for every release.

Supported Components
--------------------
The following components, organized by release, are the only ones that make
full use of the Bootstrap theme architecture.

8.0.0 (Liberty)
~~~~~~~~~~~~~~~

* `Top Navbar`_
* `Side Nav`_
* `Pie Charts`_

9.0.0 (Mitaka)
~~~~~~~~~~~~~~

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

The login splash page now uses a standard Bootstrap panel in its implementation.
See the **Panels** section in your variables file to variables to easily
customize.

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

Changing the Site Title
=======================

The OpenStack Dashboard Site Title branding (i.e. "**OpenStack** Dashboard")
can be overwritten by adding the attribute ``SITE_BRANDING``
to ``local_settings.py`` with the value being the desired name.

The file ``local_settings.py`` can be found at the Horizon directory path of
``openstack_dashboard/local/local_settings.py``.

Changing the Brand Link
=======================

The logo also acts as a hyperlink. The default behavior is to redirect to
``horizon:user_home``. By adding the attribute ``SITE_BRANDING_LINK`` with
the desired url target e.g., ``http://sample-company.com`` in
``local_settings.py``, the target of the hyperlink can be changed.

Customizing the Footer
======================

It is possible to customize the global and login footers using a theme's
template override.  Simply add ``_footer.html`` for a global footer
override or ``_login_footer.html`` for the login page's footer to your
theme's template directory.

Modifying Existing Dashboards and Panels
========================================

If you wish to alter dashboards or panels which are not part of your codebase,
you can specify a custom python module which will be loaded after the entire
Horizon site has been initialized, but prior to the URLconf construction.
This allows for common site-customization requirements such as:

* Registering or unregistering panels from an existing dashboard.
* Changing the names of dashboards and panels.
* Re-ordering panels within a dashboard or panel group.

Default Horizon panels are loaded based upon files within the openstack_dashboard/enabled/
folder.  These files are loaded based upon the filename order, with space left for more
files to be added.  There are some example files available within this folder, with the
.example suffix added.  Developers and deployers should strive to use this method of
customization as much as possible, and support for this is given preference over more
exotic methods such as monkey patching and overrides files.

Horizon customization module (overrides)
========================================

Horizon has a global overrides mechanism available to perform customizations that are not
yet customizable via configuration settings.  This file can perform monkey patching and
other forms of customization which are not possible via the enabled folder's customization
method.

This method of customization is meant to be available for deployers of Horizon, and use of
this should be avoided by Horizon plugins at all cost.  Plugins needing this level of
monkey patching and flexibility should instead look for changing their __init__.py file
and performing customizations through other means.

To specify the python module containing your modifications, add the key
``customization_module`` to your ``HORIZON_CONFIG`` dictionary in
``local_settings.py``. The value should be a string containing the path to your
module in dotted python path notation. Example::

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

You cannot unregister a ``default_panel``. If you wish to remove a
``default_panel``, you need to make a different panel in the dashboard as a
``default_panel`` and then unregister the former. For example, if you wished
to remove the ``overview_panel`` from the ``Project`` dashboard, you could do
the following::

    project = horizon.get_dashboard('project')
    project.default_panel = "instances"
    overview = project.get_panel('overview')
    project.unregister(overview.__class__)

You can also override existing methods with your own versions::

    # Disable Floating IPs
    from openstack_dashboard.dashboards.project.access_and_security import tabs
    from openstack_dashboard.dashboards.project.instances import tables

    NO = lambda *x: False

    tabs.FloatingIPsTab.allowed = NO
    tables.AssociateIP.allowed = NO
    tables.SimpleAssociateIP.allowed = NO
    tables.SimpleDisassociateIP.allowed = NO

You could also customize what columns are displayed in an existing
table, by redefining the ``columns`` attribute of its ``Meta``
class. This can be achieved in 3 steps:

#. Extend the table that you wish to modify
#. Redefine the ``columns`` attribute under the ``Meta`` class for this
   new table
#. Modify the ``table_class`` attribute for the related view so that it
   points to the new table


For example, if you wished to remove the Admin State column from the
:class:`~openstack_dashboard.dashboards.admin.networks.tables.NetworksTable`,
you could do the following::

    from openstack_dashboard.dashboards.project.networks import tables
    from openstack_dashboard.dashboards.project.networks import views

    class MyNetworksTable(tables.NetworksTable):

        class Meta(tables.NetworksTable.Meta):
            columns = ('name', 'subnets', 'shared', 'status')

    views.IndexView.table_class = MyNetworksTable

If you want to add a column you can override the parent table in a
similar way, add the new column definition and then use the ``Meta``
``columns`` attribute to control the column order as needed.

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


Icons
=====

Horizon uses font icons from Font Awesome.  Please see `Font Awesome`_ for
instructions on how to use icons in the code.

To add icon to Table Action, use icon property. Example:

    class CreateSnapshot(tables.LinkAction):
       name = "snapshot"
       verbose_name = _("Create Snapshot")
       icon = "camera"

Additionally, the site-wide default button classes can be configured by
setting ``ACTION_CSS_CLASSES`` to a tuple of the classes you wish to appear
on all action buttons in your ``local_settings.py`` file.


Custom Stylesheets
==================

It is possible to define custom stylesheets for your dashboards. Horizon's base
template ``openstack_dashboard/templates/base.html`` defines multiple blocks that
can be overridden.

To define custom css files that apply only to a specific dashboard, create
a base template in your dashboard's templates folder, which extends Horizon's
base template e.g. ``openstack_dashboard/dashboards/my_custom_dashboard/
templates/my_custom_dashboard/base.html``.

In this template, redefine ``block css``. (Don't forget to include
``_stylesheets.html`` which includes all Horizon's default stylesheets.)::

    {% extends 'base.html' %}

    {% block css %}
      {% include "_stylesheets.html" %}

      {% load compress %}
      {% compress css %}
      <link href='{{ STATIC_URL }}my_custom_dashboard/scss/my_custom_dashboard.scss' type='text/scss' media='screen' rel='stylesheet' />
      {% endcompress %}
    {% endblock %}

The custom stylesheets then reside in the dashboard's own ``static`` folder
``openstack_dashboard/dashboards/my_custom_dashboard/static/
my_custom_dashboard/scss/my_custom_dashboard.scss``.

All dashboard's templates have to inherit from dashboard's base.html::

    {% extends 'my_custom_dashboard/base.html' %}
    ...


Custom Javascript
=================

Similarly to adding custom styling (see above), it is possible to include
custom javascript files.

All Horizon's javascript files are listed in the ``openstack_dashboard/
templates/horizon/_scripts.html`` partial template, which is included in
Horizon's base template in ``block js``.

To add custom javascript files, create an ``_scripts.html`` partial template in
your dashboard ``openstack_dashboard/dashboards/my_custom_dashboard/
templates/my_custom_dashboard/_scripts.html`` which extends
``horizon/_scripts.html``. In this template override the
``block custom_js_files`` including your custom javascript files::

    {% extends 'horizon/_scripts.html' %}

    {% block custom_js_files %}
        <script src='{{ STATIC_URL }}my_custom_dashboard/js/my_custom_js.js' type='text/javascript' charset='utf-8'></script>
    {% endblock %}


In your dashboard's own base template ``openstack_dashboard/dashboards/
my_custom_dashboard/templates/my_custom_dashboard/base.html`` override
``block js`` with inclusion of dashboard's own ``_scripts.html``::

    {% block js %}
        {% include "my_custom_dashboard/_scripts.html" %}
    {% endblock %}

The result is a single compressed js file consisting both Horizon and
dashboard's custom scripts.

Additionally, some marketing and analytics scripts require you to place them
within the page's <head> tag. To do this, place them within the
``horizon/_custom_head_js.html`` file. Similar to the ``_scripts.html`` file
mentioned above, you may link to an existing file::

    <script src='{{ STATIC_URL }}/my_custom_dashboard/js/my_marketing_js.js' type='text/javascript' charset='utf-8'></script>

or you can paste your script directly in the file, being sure to use
appropriate tags::

  <script type="text/javascript">
  //some javascript
  </script>


Customizing Meta Attributes
===========================

To add custom metadata attributes to your project's base template, include
them in the ``horizon/_custom_meta.html`` file. The contents of this file will be
inserted into the page's <head> just after the default Horizon meta tags.

..  _Bootswatch: http://bootswatch.com
..  _Bootswatchr: http://bootswatchr.com/create#!
..  _Paintstrap: http://paintstrap.com
..  _Bootstrap: http://getbootstrap.com/customize/
..  _Google's Material Design: https://www.google.com/design/spec/material-design/introduction.html
..  _Font Awesome: https://fortawesome.github.io/Font-Awesome/
