==================
JavaScript Testing
==================

There are multiple components in our JavaScript testing framework:
  * `Jasmine`_ is our testing framework, so this defines the syntax and file
    structure we use to test our JavaScript.
  * `Karma`_ is our test runner. Amongst other things, this lets us run the
    tests against multiple browsers and generate test coverage reports.
    Alternatively, tests can be run inside the browser with the Jasmine spec
    runner.
  * `PhantomJS`_ provides a headless WebKit (the browser engine). This gives us
    native support for many web features without relying on specific browsers
    being installed.
  * `ESLint`_ is a pluggable code linting utility. This will catch small errors
    and inconsistencies in your JS, which may lead to bigger issues later on.
    See :ref:`js_code_style` for more detail.

Jasmine uses specs (``.spec.js``) which are kept with the JavaScript files
that they are testing. See the :ref:`js_file_structure` section or the `Examples`_
below for more detail on this.

.. _Jasmine: https://jasmine.github.io/2.3/introduction.html
.. _Karma: https://karma-runner.github.io/
.. _PhantomJS: http://phantomjs.org/
.. _ESLint: http://eslint.org/

Running Tests
=============

Tests can be run in two ways:

  1. Open <dev_server_ip:port>/jasmine in a browser. The development server can be
     run with ``./run_tests.sh --runserver`` from the horizon root directory.
  2. ``npm run test`` from the horizon root directory. This runs Karma,
     so it will run all the tests against PhantomJS and generate coverage
     reports.

The code linting job can be run with ``npm run lint``.

Coverage Reports
----------------

Our Karma setup includes a plugin to generate test coverage reports. When
developing, be sure to check the coverage reports on the master branch and
compare your development branch; this will help identify missing tests.

To generate coverage reports, run ``npm run test``. The coverage reports can be
found at ``horizon/coverage-karma/`` (framework tests) and
``openstack_dashboard/coverage-karma/`` (dashboard tests). Load
``<browser>/index.html`` in a browser to view the reports.

Writing Tests
=============

Jasmine uses suites and specs:
  * Suites begin with a call to ``describe``, which takes two parameters; a
    string and a function. The string is a name or title for the spec suite,
    whilst the function is a block that implements the suite.
  * Specs begin with a call to ``it``, which also takes a string and a function
    as parameters. The string is a name or title, whilst the function is a
    block with one or more expectations (``expect``) that test the state of
    the code. An expectation in Jasmine is an assertion that is either true or
    false; every expectation in a spec must be true for the spec to pass.

``.spec.js`` files can be handled manually or automatically. To use the
automatic file discovery add::

    AUTO_DISCOVER_STATIC_FILES = True

to your enabled file. JS code for testing should use the extensions
``.mock.js`` and ``.spec.js``.

You can read more about the functionality in the
:ref:`auto_discover_static_files` section of the settings documentation.

To manually add specs, add the following array and relevant file paths to your
enabled file:
::

  ADD_JS_SPEC_FILES = [
    ...
    'path_to/my_angular_code.spec.js',
    ...
  ]

Examples
========

.. Note::
  The code below is just for example purposes, and may not be current in
  horizon. Ellipses (...) are used to represent code that has been
  removed for the sake of brevity.

Example 1 - A reusable component in the **horizon** directory
-------------------------------------------------------------

File tree:
::

  horizon/static/framework/widgets/modal
  ├── modal.controller.js
  ├── modal.module.js
  ├── modal.service.js
  └── modal.spec.js

Lines added to ``horizon/test/jasmine/jasmine_tests.py``:
::

  class ServicesTests(test.JasmineTests):
    sources = [
      ...
      'framework/widgets/modal/modal.module.js',
      'framework/widgets/modal/modal.controller.js',
      'framework/widgets/modal/modal.service.js',
      ...
    ]

    specs = [
      ...
      'framework/widgets/modal/modal.spec.js',
      ...
    ]

``modal.spec.js``:
::

  ...

  (function() {
    "use strict";

    describe('horizon.framework.widgets.modal module', function() {

      beforeEach(module('horizon.framework'));

      describe('simpleModalCtrl', function() {
        var scope;
        var modalInstance;
        var context;
        var ctrl;

        beforeEach(inject(function($controller) {
          scope = {};
          modalInstance = {
            close: function() {},
            dismiss: function() {}
          };
          context = { what: 'is it' };
          ctrl = $controller('simpleModalCtrl', {
                 $scope: scope,
                 $modalInstance: modalInstance,
                 context: context
          });
        }));

        it('establishes a controller', function() {
          expect(ctrl).toBeDefined();
        });

        it('sets context on the scope', function() {
          expect(scope.context).toBeDefined();
          expect(scope.context).toEqual({ what: 'is it' });
        });

        it('sets action functions', function() {
          expect(scope.submit).toBeDefined();
          expect(scope.cancel).toBeDefined();
        });

        it('makes submit close the modal instance', function() {
          expect(scope.submit).toBeDefined();
          spyOn(modalInstance, 'close');
          scope.submit();
          expect(modalInstance.close.calls.count()).toBe(1);
        });

        it('makes cancel close the modal instance', function() {
          expect(scope.cancel).toBeDefined();
          spyOn(modalInstance, 'dismiss');
          scope.cancel();
          expect(modalInstance.dismiss).toHaveBeenCalledWith('cancel');
        });
      });

      ...

    });
  })();

Example 2 - Panel-specific code in the **openstack_dashboard** directory
------------------------------------------------------------------------

File tree:
::

  openstack_dashboard/static/dashboard/launch-instance/network/
  ├── network.help.html
  ├── network.html
  ├── network.js
  ├── network.scss
  └── network.spec.js


Lines added to ``openstack_dashboard/enabled/_10_project.py``:
::

  LAUNCH_INST = 'dashboard/launch-instance/'

  ADD_JS_FILES = [
    ...
    LAUNCH_INST + 'network/network.js',
    ...
  ]

  ADD_JS_SPEC_FILES = [
    ...
    LAUNCH_INST + 'network/network.spec.js',
    ...
  ]

``network.spec.js``:
::

  ...

  (function(){
    'use strict';

    describe('Launch Instance Network Step', function() {

      describe('LaunchInstanceNetworkCtrl', function() {
        var scope;
        var ctrl;

        beforeEach(module('horizon.dashboard.project.workflow.launch-instance'));

        beforeEach(inject(function($controller) {
          scope = {
            model: {
              newInstanceSpec: {networks: ['net-a']},
              networks: ['net-a', 'net-b']
            }
          };
          ctrl = $controller('LaunchInstanceNetworkCtrl', {$scope:scope});
        }));

        it('has correct network statuses', function() {
          expect(ctrl.networkStatuses).toBeDefined();
          expect(ctrl.networkStatuses.ACTIVE).toBeDefined();
          expect(ctrl.networkStatuses.DOWN).toBeDefined();
          expect(Object.keys(ctrl.networkStatuses).length).toBe(2);
        });

        it('has correct network admin states', function() {
          expect(ctrl.networkAdminStates).toBeDefined();
          expect(ctrl.networkAdminStates.UP).toBeDefined();
          expect(ctrl.networkAdminStates.DOWN).toBeDefined();
          expect(Object.keys(ctrl.networkStatuses).length).toBe(2);
        });

        it('defines a multiple-allocation table', function() {
          expect(ctrl.tableLimits).toBeDefined();
          expect(ctrl.tableLimits.maxAllocation).toBe(-1);
        });

        it('contains its own labels', function() {
          expect(ctrl.label).toBeDefined();
          expect(Object.keys(ctrl.label).length).toBeGreaterThan(0);
        });

        it('contains help text for the table', function() {
          expect(ctrl.tableHelpText).toBeDefined();
          expect(ctrl.tableHelpText.allocHelpText).toBeDefined();
          expect(ctrl.tableHelpText.availHelpText).toBeDefined();
        });

        it('uses scope to set table data', function() {
          expect(ctrl.tableDataMulti).toBeDefined();
          expect(ctrl.tableDataMulti.available).toEqual(['net-a', 'net-b']);
          expect(ctrl.tableDataMulti.allocated).toEqual(['net-a']);
          expect(ctrl.tableDataMulti.displayedAllocated).toEqual([]);
          expect(ctrl.tableDataMulti.displayedAvailable).toEqual([]);
        });
      });

      ...

    });
  })();
