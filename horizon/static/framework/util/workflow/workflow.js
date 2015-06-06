(function () {
  'use strict';

  /**
   * @ngdoc overview
   * @name horizon.framework.util.workflow
   * @description
   *
   * # horizon.framework.util.workflow
   *
   * This module provides utility function service `workflow` to allow
   * decorating a workflow object.  A user (developer) friendly workflow
   * specification object can be shaped into a format that is friendly to
   * {@link horizon.framework.widgets.wizard `wizard`} by utilizing this service.
   *
   * The service provides a mechanism of decoupling general wizard UI component
   * from business components.
   *
   * | Factories                                                               |
   * |--------------------------------------------------------------------------|
   * | {@link horizon.framework.util.workflow.factory:workflow `workflow`}                |
   *
   */

  angular.module('horizon.framework.util.workflow', [])

  /**
   * @ngdoc factory
   * @name horizon.framework.util.workflow.factory:workflow
   * @module horizon.framework.util.workflow
   * @kind function
   * @description
   *
   * Decorate the workflow specification object with specified decorators.
   *
   * @param {Object} The input workflow specification object
   * @param {Array<function>} decorators A list a decorator functions.
   *
   * @returns {Object} The decorated workflow specification object, the same
   * reference to the input spec object.
   *
   ```js

    angular.module('MyModule', [])

      .factory('myService', ['$q', 'horizon.framework.util.workflow.service', function ($q, workflow) {

        // a workflow specification object:
        var spec = {
              steps: [
                { requireSomeServices: true },
                { },
                { requireSomeServices: true }
              ]
            };

        // define some decorators
        var decorators = [
              // a decorator
              function (spec) {
                var steps = spec.steps;

                angular.forEach(steps, function (step) {
                  if (step.requireSomeServices) {
                    step.checkReadiness = function () {
                      var d = $q.defer();

                      // checking if the service is available asynchronously .
                      setTimeout(function () {
                        d.resolve();
                      }, 500);

                      return d.promise;
                    };
                  }
                });
              },

              // another decorator
              function (spec) {
                //...
              }
            ];

        return workflow(spec, decorators);
      }]);
   ```
   */

  .factory('horizon.framework.util.workflow.service', [
    function () {
      return function (spec, decorators) {
        angular.forEach(decorators, function (decorator) {
          decorator(spec);
        });
        return spec;
      };
    }
  ]);
})();
