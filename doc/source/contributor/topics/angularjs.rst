.. _topics-angularjs:

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
`via a package manager <https://github.com/nodejs/node-v0.x-archive/wiki/Installing-Node.js-via-package-manager>`_.

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
horizon root directory with ``tox -e npm -- lint``, or alternatively on a
specific directory or file with ``eslint file.js``.

Horizon includes a `.eslintrc` in its root directory, that is used by the
local tests. An explanation of the options, and details of others you may want
to use, can be found in the
`ESLint user guide <https://eslint.org/docs/user-guide/configuring>`_.

Application Structure
=====================

OpenStack Dashboard is an example of a Horizon-based Angular application. Other
applications built on the Horizon framework can follow a similar structure. It
is composed of two key Angular modules:

**app.module.js** - The root of the application. Defines the modules required by
    the application, and includes modules from its pluggable dashboards.

**framework.module.js** - Reusable Horizon components. It is one of the
    application dependencies.

.. _js_file_structure:

File Structure
==============

Horizon has three kinds of angular code:

1. Specific to one dashboard in the OpenStack Dashboard application
2. Specific to the OpenStack Dashboard application, but reusable by multiple
   dashboards
3. Reusable by any application based on the Horizon framework

When adding code to horizon, consider whether it is dashboard-specific or
should be broken out as a reusable utility or widget.

Code specific to one dashboard
------------------------------

Code that isn't shared beyond a single dashboard is placed in
``openstack_dashboard/dashboards/mydashboard/static``. Entire dashboards may be
enabled or disabled using Horizon's plugin mechanism. Therefore no dashboards
other than ``mydashboard`` can safely use this code.

The ``openstack_dashboard/dashboards/mydashboard/static`` directory structure
determines how the code is deployed and matches the module structure.
For example:
::

  openstack_dashboard/dashboards/identity/static/dashboard/identity/
  ├── identity.module.js
  ├── identity.module.spec.js
  └── identity.scss

Because the code is in ``openstack_dashboard/dashboards/identity`` we know it
is specific to just the ``identity`` dashboard and not used by any others.

Code shared by multiple dashboards
----------------------------------

Views or utilities needed by multiple dashboards are placed in
``openstack_dashboard/static/app``. For example:
::

  openstack_dashboard/static/app/core/cloud-services/
  ├── cloud-services.module.js
  ├── cloud-services.spec.js
  ├── hz-if-settings.directive.js
  └── hz-if-settings.directive.spec.js

The ``cloud-services`` module is used by panels in multiple dashboards. It
cannot be placed within ``openstack_dashboard/dashboards/mydashboard`` because
disabling that one dashboard would break others. Therefore, it is included as
part of the application ``core`` module. Code in ``app/`` is guaranteed to
always be present, even if all other dashboards are disabled.

Reusable components
-------------------

Finally, components that are easily reused by any application are placed in
``horizon/static/framework/``. These do not contain URLs or business logic
that is specific to any application (even the OpenStack Dashboard application).

The modal directive ``horizon/static/framework/widgets/modal/`` is a good
example of a reusable component.

One folder per component
------------------------

Each component should have its own folder, with the code broken up into one JS
component per file. (See `Single Responsibility <https://github.com/johnpapa/angular-styleguide#single-responsibility>`_
in the style guide).
Each folder may include styling (``*.scss``), as well as templates (``*.html``)
and tests (``*.spec.js``).
You may also include examples, by appending ``.example``.

For larger components, such as workflows with multiple steps, consider breaking
the code down further. For example, the Launch Instance workflow, has one
directory per step. See
``openstack_dashboard/dashboards/project/static/dashboard/project/workflow/launch-instance/``

SCSS files
----------

The top-level SCSS file in ``openstack_dashboard/static/app/_app.scss``. It
includes any styling that is part of the application ``core`` and may be
reused by multiple dashboards. SCSS files that are specific to a particular
dashboard are linked to the application by adding them in that dashboard's
enabled file. For example, `_1920_project_containers_panel.py` is the enabled
file for the ``Project`` dashboard's ``Container`` panel and includes:
::

    ADD_SCSS_FILES = [
        'dashboard/project/containers/_containers.scss',
    ]

Styling files are hierarchical, and include any direct child SCSS files. For
example, ``project.scss`` would includes the ``workflow`` SCSS file, which in
turn includes any launch instance styling:
::

    @import "workflow/workflow";

This allows the application to easily include all needed styling, simply by
including a dashboard's top-level SCSS file.

Module Structure
================

Horizon Angular modules use names that map to the source code directory
structure. This provides namespace isolation for modules and services, which
makes dependency injection clearer. It also reduces code conflicts where two
different modules define a module, service or constant of the same name. For
example:
::

  openstack_dashboard/dashboards/identity/static/dashboard/identity/
  └── identity.module.js

The preferred Angular module name in this example is
``horizon.dashboard.identity``. The ``horizon`` part of the module name maps to
the ``static`` directory and indicates this is a ``horizon`` based application.
``dashboard.identity`` maps to folders that are created within ``static``. This
allows a direct mapping between the angular module name of
``horizon.dashboard.identity`` and the source code directory of
``static\dashboard\identity``.

Services and constants within these modules should all start with their module
name to avoid dependency injection collisions. For example:
::

    $provide.constant('horizon.dashboard.identity.basePath', path);

Directives do not require the module name but are encouraged to begin with the
``hz`` prefix. For example:
::

    .directive('hzMagicSearchBar', hzMagicSearchBar);

Finally, each module lists its child modules as a dependency. This allows the
root module to be included by an application, which will automatically define
all child modules. For example:
::

    .module('horizon.framework', [
      'horizon.framework.conf',
      'horizon.framework.util',
      'horizon.framework.widgets'
    ])

``horizon.framework`` declares a dependency on ``horizon.framework.widgets``,
which declares dependencies on each individual widget. This allows the
application to access any widget, simply by depending on the top-level
``horizon.framework`` module.

Testing
=======

1. Open <dev_server_ip:port>/jasmine in a browser. The development server can
   be run with ``tox -e runserver`` from the horizon root directory; by
   default, this will run the development server at ``http://localhost:8000``.
2. ``tox -e npm`` from the horizon root directory.

The code linting job can be run with ``tox -e npm -- lint``. If there are many
warnings, you can also use ``tox -e npm -- lintq`` to see only errors and
ignore warnings.

For more detailed information, see :ref:`topics-javascript-testing`.

Translation (Internationalization and Localization)
===================================================

See :ref:`making_strings_translatable` for information on the translation
architecture and how to ensure your code is translatable.

Creating your own panel
=======================

.. Note::
  This section will be extended as standard practices are adopted upstream.
  Currently, it may be useful to look at the Project Images Panel as a
  complete reference. Since Newton, it is Angular by default (set to True in the
  ANGULAR_FEATURES dict in ``settings.py``).
  You may track all the changes made to the Image Panel
  `here <https://github.com/openstack/horizon/commits/master/openstack_dashboard/static/app/core/images>`__

.. Note::
  Currently, Angular module names must still be manually declared with
  ``ADD_ANGULAR_MODULES``, even when using automatic file discovery.

This section serves as a basic introduction to writing your own panel for
horizon, using AngularJS. A panel may be included with the plugin system, or it
may be part of the upstream horizon project.

Upstream
--------

JavaScript files can be discovered automatically, handled manually, or a mix of
the two. Where possible, use the automated mechanism.
To use the automatic functionality, add::

    AUTO_DISCOVER_STATIC_FILES = True

to your enabled file (``enabled/<plugin_name>.py``). To make this possible,
you need to follow some structural conventions:

- Static files should be put in a ``static/`` folder, which should be found
  directly under the folder for the dashboard/panel/panel groups Python
  package.
- JS code that defines an Angular module should be in a file with extension of
  ``.module.js``.
- JS code for testing should be named with extension of ``.mock.js`` and of
  ``.spec.js``.
- Angular templates should have extension of ``.html``.

You can read more about the functionality in the
:ref:`auto_discover_static_files` section of the settings documentation.

To manually add files, add the following arrays and file paths to the enabled
file:
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
    'my.angular.code',
    ...
  ]

Plugins
-------

Add a new panel/ panel group/ dashboard (See :ref:`tutorials-dashboard`).
JavaScript file inclusion is the same as the Upstream process.

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

Schema Forms
============

`JSON schemas`_ are used to define model layout and then `angular-schema-form`_
is used to create forms from that schema. Horizon adds some functionality on
top of that to make things even easier through ``ModalFormService`` which will
open a modal with the form inside.

A very simple example::

  var schema = {
    type: "object",
    properties: {
      name: { type: "string", minLength: 2, title: "Name", description: "Name or alias" },
      title: {
        type: "string",
        enum: ['dr','jr','sir','mrs','mr','NaN','dj']
      }
    }
  };
  var model = {name: '', title: ''};
  var config = {
    title: gettext('Create Container'),
    schema: schema,
    form: ['*'],
    model: model
  };
  ModalFormService.open(config).then(submit);   // returns a promise

  function submit() {
    // do something with model.name and model.title
  }

.. _JSON schemas: http://json-schema.org/
.. _angular-schema-form: https://github.com/json-schema-form/angular-schema-form/blob/master/docs/index.md
