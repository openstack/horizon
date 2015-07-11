=====================
AngularJS Topic Guide
=====================

.. Note::
  This guide is a work in progress. It has been uploaded to encourage faster
  reviewing and code development in Angular, and to help the community
  standardize on a set of guidelines. There are notes inline on sections
  that are likely to change soon, and the docs will be updated promptly
  after any changes.

Getting Started
===============

The tooling for AngularJS testing and code linting relies on npm, the
node package manager, and thus relies on Node.js. While it is not a
prerequisite to developing with Horizon, it is advisable to install Node.js,
either through `downloading <https://nodejs.org/download/>`_ or
`via a package manager <https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager>`_.

Once you have npm available on your system, run ``npm install`` from the
horizon root directory.

.. _js_code_style:

Code Style
==========

We currently use the `Angular Style Guide`_ by John Papa as reference material.
When reviewing AngularJS code, it is helpful to link directly to the style
guide to reinforce a point, e.g.
https://github.com/johnpapa/angular-styleguide#style-y024

.. _Angular Style Guide: https://github.com/johnpapa/angular-styleguide

ESLint
------

ESLint is a tool for identifying and reporting on patterns in your JS code, and
is part of the automated tests run by Jenkins. You can run ESLint from the
horizon root directory with ``npm run lint``, or alternatively on a specific
directory or file with ``eslint file.js``.

Horizon includes a `.eslintrc` in its root directory, that is used by the
local tests. An explanation of the options, and details of others you may want
to use, can be found in the
`ESLint user guide <http://eslint.org/docs/user-guide/configuring>`_.

.. _js_file_structure:

File Structure
==============

Each component should have its own folder, with the code broken up into one JS
component per file. (See `Single Responsibility <https://github.com/johnpapa/angular-styleguide#single-responsibility>`_
in the style guide).
Each folder may include styling (``.scss``), as well as templates(``.html``)
and tests (``.spec.js``).
You may also include examples, by appending ``.example``.

Reusable components are in ``horizon/static/framework/``. These are a
collection of pieces, such as modals or wizards where the functionality
is likely to be used across many parts of horizon.
When adding code to horizon, consider whether it is panel-specific or should be
broken out as a reusable utility or widget.

The modal directive is a good example of the file structure. This is a reusable
component:
::

  horizon/static/framework/widgets/modal/
  ├── modal.controller.js
  ├── modal.module.js
  ├── modal.service.js
  ├── modal.spec.js
  └── simple-modal.html

Panel-specific code is in ``openstack_dashboard/static/dashboard/``. For example:
::

  openstack_dashboard/static/dashboard/workflow/
  ├── decorator.service.js
  ├── workflow.module.js
  ├── workflow.module.spec.js
  └── workflow.service.js

For larger components, such as workflows with multiple steps, consider breaking
the code down further. The Angular **Launch Instance** workflow,
for example, has one directory per step
(``openstack_dashboard/static/dashboard/launch-instance/``)

Testing
=======

1. Open <dev_server_ip:port>/jasmine in a browser. The development server can be run
   with``./run_tests.sh --runserver`` from the horizon root directory.
2. ``npm run test`` from the horizon root directory.

The code linting job can be run with ``npm run lint``.

For more detailed information, see :doc:`javascript_testing`.

Translation (Internationalization and Localization)
===================================================

.. Note::
  This is likely to change soon, after the
  `Angular Translation <https://blueprints.launchpad.net/horizon/+spec/angular-translate-makemessages>`_
  blueprint has been completed.

Translations are handled in Transifex, as with Django. They are merged daily
with the horizon upstream codebase. See
`Translations <https://wiki.openstack.org/wiki/Translations>`_ in the
OpenStack wiki to learn more about this process.

Use either ``gettext`` (singular) or ``ngettext`` (plural):
::

  gettext('text to be translated');
  ngettext('text to be translated');

The :ref:`translatability` section contains information about the
pseudo translation tool, and how to make sure your translations are working
locally.

Creating your own panel
=======================

.. Note::
  This section will be extended as standard practices are adopted upstream.
  Currently, it may be useful to use
  `this patch <https://review.openstack.org/#/c/190852/>`_ and its dependants
  as an example.

.. Note::
  Currently, Angular module names must still be manually declared with
  ``ADD_ANGULAR_MODULES``, even when using automatic file discovery.

This section serves as a basic introduction to writing your own panel for
horizon, using AngularJS. A panel may be included with the plugin system, or it may be
part of the upstream horizon project.

Upstream
--------

JavaScript files can be discovered automatically, handled manually, or a mix of
the two. Where possible, use the automated mechanism.
To use the automatic functionality, add::
  AUTO_DISCOVER_STATIC_FILES = True
to your enabled file (``enabled/<plugin_name>.py``). To make this possible,
you need to follow some structural conventions:

  - Static files should be put in a ``static/`` folder, which should be found directly under
    the folder for the dashboard/panel/panel groups Python package.
  - JS code that defines an Angular module should be in a file with extension of ``.module.js``.
  - JS code for testing should be named with extension of ``.mock.js`` and of ``.spec.js``.
  - Angular templates should have extension of ``.html``.

You can read more about the functionality in the
:ref:`auto_discover_static_files` section of the settings documentation.

To manually add files, add the following arrays and file paths to the enabled file:
::

  ADD_JS_FILES = [
    ...
    'path-to/my-angular-code.js',
    ...
  ]

  ADD_JS_SPEC_FILES = [
    ...
    'path-to/my-angular-code.spec.js',
    ...
  ]

  ADD_ANGULAR_MODULES = [
    ...
    'angular.module',
    ...
  ]

Plugins
-------

Add a new panel/ panel group/ dashboard (See :doc:`tutorial`). JavaScript file
inclusion is the same as the Upstream process.

To include external stylesheets, you must ensure that ``ADD_SCSS_FILES`` is
defined in your enabled file, and add the relevant filepath, as below:
::

  ADD_SCSS_FILES = [
    ...
    'path-to/my-styles.scss',
    ...
  ]

.. Note::
  We highly recommend using a single SCSS file for your plugin. SCSS supports
  nesting with @import, so if you have multiple files (i.e. per panel styling)
  it is best to import them all into one, and include that single file. You can
  read more in the `SASS documentation`_.

.. _SASS documentation: http://sass-lang.com/documentation/file.SASS_REFERENCE.html#import
