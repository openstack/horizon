======
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
``local_settings.py`` to a list of tuples, such that
``('name', 'label', 'path')``

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
For a full list of the Dashboard SCSS variables that can be changed,
see the variables file at
``openstack_dashboard/static/dashboard/scss/_variables.scss``.

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

Once you have made your changes you must re-generate the static files with:

.. code-block:: console

   python manage.py collectstatic

By default, all of the themes configured by ``AVAILABLE_THEMES`` setting are
collected by horizon during the `collectstatic` process. By default, the themes
are collected into the dynamic `static/themes` directory, but this location can
be customized via the ``local_settings.py`` variable: ``THEME_COLLECTION_DIR``

Once collected, any theme configured via ``AVAILABLE_THEMES`` is available to
inherit from by importing its variables and styles from its collection
directory.  The following is an example of inheriting from the material theme::

  @import "/themes/material/variables";
  @import "/themes/material/styles";

All themes will need to be configured in ``AVAILABLE_THEMES`` to allow
inheritance.  If you wish to inherit from a theme, but not show that theme
as a selectable option in the theme picker widget, then simply configure the
``SELECTABLE_THEMES`` to exclude the parent theme.  ``SELECTABLE_THEMES`` must
be of the same format as ``AVAILABLE_THEMES``.  It defaults to
``AVAILABLE_THEMES`` if it is not set explicitly.

Bootswatch
~~~~~~~~~~

Horizon packages the Bootswatch SCSS files for use with its ``material`` theme.
Because of this, it is simple to use an existing Bootswatch theme as a base.
This is due to the fact that Bootswatch is loaded as a 3rd party static asset,
and therefore is automatically collected into the `static` directory in
`/horizon/lib/`.  The following is an example of how to inherit from
Bootswatch's ``darkly`` theme::

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

These assets include logo.svg, splash-logo.svg and favicon.ico, however
overriding the SVG/GIF assets used by Heat within the `dashboard/img` folder
is not currently supported.

Customizing the Logo
--------------------

Simple
~~~~~~

If you wish to customize the logo that is used on the splash screen or in the
top navigation bar, then you need to create an ``img`` directory under your
theme's static root directory and place your custom ``logo.svg`` or
``logo-splash.svg`` within it.

If you wish to override the ``logo.svg`` using the previous method, and if the
image used is larger than the height of the top navigation, then the image will
be constrained to fit within the height of nav.  You can customize the height
of the top navigation bar by customizing the SCSS variable: ``$navbar-height``.
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
