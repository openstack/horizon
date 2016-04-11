=========================
Styling in Horizon (SCSS)
=========================

Horizon uses `SCSS`_ (not to be confused with Sass) to style its HTML. This
guide is targeted at developers adding code to upstream Horizon. For
information on creating your own branding/theming, see :doc:`customizing`.

.. _SCSS: http://sass-lang.com/guide

Code Layout
===========

The base SCSS can be found at ``openstack_dashboard/static/dashboard/scss/``.
This directory should **only** contain the minimal styling for functionality;
code that isn't configurable by themes. ``horizon.scss`` is a top level file
that imports from the ``components/`` directory, as well as other base styling
files; potentially some basic page layout rules that Horizon relies on to
function.

.. Note::
  Currently, a great deal of theming is also kept in the ``horizon.scss`` file
  in this directory, but that will be reduced as we proceed with the new code
  design.

Horizon's ``default`` theme stylesheets can be found at
``openstack_dashboard/themes/default/``.

::

  ├── _styles.scss
  ├── _variables.scss
  ├── bootstrap/
      └── ...
  └── horizon/
      └── ...

The top level ``_styles.scss`` and ``_variables.scss`` contain imports from
the ``bootstrap`` and ``horizon`` directories.

The "bootstrap" directory
-------------------------

This directory contains overrides and customization of Bootstrap variables, and
markup used by Bootstrap components. This should **only** override existing
Bootstrap content. For examples of these components, see the
`Theme Preview Page`_.

::

  bootstrap/
  ├── _styles.scss
  ├── _variables.scss
  └── components/
      ├── _component_0.scss
      ├── _component_1.scss
      └── ...

- ``_styles.scss`` imports the SCSS defined for each component.
- ``_variables.scss`` contains the definitions for every Bootstrap variable.
  These variables can be altered to affect the look and feel of Horizon's
  default theme.
- The ``components`` directory contains overrides for Bootstrap components,
  such as tables or navbars.

The "horizon" directory
-----------------------

This directory contains SCSS that is absolutely specific to Horizon; code here
should **not** override existing Bootstrap content, such as variables and rules.

::

  horizon/
  ├── _styles.scss
  ├── _variables.scss
  └── components/
      ├── _component_0.scss
      ├── _component_1.scss
      └── ...

- ``_styles.scss`` imports the SCSS defined for each component. It may also
  contain some minor styling overrides.
- ``_variables.scss`` contains variable definitions that are specific to the
  horizon theme. This should **not** override any bootstrap variables, only
  define new ones. You can however, inherit bootstrap variables for reuse
  (and are encouraged to do so where possible).
- The ``components`` directory contains styling for each individual component
  defined by Horizon, such as the sidebar or pie charts.

Adding new SCSS
===============

To keep Horizon easily themable, there are several code design guidelines that
should be adhered to:

- Reuse Bootstrap variables where possible. This allows themes to influence
  styling by simply overriding a few existing variables, instead of rewriting
  large chunks of the SCSS files.
- If you are unable to use existing variables - such as for very specific
  functionality - keep the new rules as specific as possible to your component
  so they do not cause issues in unexpected places.
- Check if existing components suit your use case. There may be existing
  components defined by Bootstrap or Horizon that can be reused, rather than
  writing new ones.

Theme Preview Page
==================

When the :ref:`DEBUG <debug_setting>` setting is set to ``True``, the Developer
dashboard will be present in Horizon's side nav. The Bootstrap Theme Preview
panel contains examples of all stock Bootstrap markup with the currently
applied theme, as well as source code for replicating them; click the ``</>``
symbol when hovering over a component.

Alternate Theme
===============

A second theme is provided by default at
``openstack_dashboard/themes/material/``. When adding new SCSS to horizon, you
should check that it does not interfere with the Material theme. Images of how
the Material theme should look can be found at https://bootswatch.com/paper/.
This theme is now configured to run as the alternate theme within Horizon.
