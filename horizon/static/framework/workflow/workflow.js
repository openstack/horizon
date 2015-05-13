(function () {
  'use strict';

  /**
   * @ngdoc overview
   * @name hz.framework.workflow
   * @description
   *
   * # hz.framework.workflow
   *
   * This module provides utility function service `workflow` to allow
   * decorating a workflow object.  A user (developer) friendly workflow
   * specification object can be shaped into a format that is friendly to
   * {@link hz.widget.wizard `wizard`} by utilizing this service.
   *
   * The service provides a mechanism of decoupling general wizard UI component
   * from business components.
   *
   * | Factories                                                               |
   * |--------------------------------------------------------------------------|
   * | {@link hz.framework.workflow.factory:workflow `workflow`}                |
   *
   */

  angular.module('hz.framework.workflow', [])

  /**
   * @ngdoc factory
   * @name hz.framework.workflow.factory:workflow
   * @module hz.framework.workflow
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

      .factory('myService', ['$q', 'workflow', function ($q, workflow) {

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

  .factory('workflow', [
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
