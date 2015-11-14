/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 *    (c) Copyright 2015 ThoughtWorks, Inc.
 *    Copyright 2015 IBM Corp.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function() {
  'use strict';

  angular
    .module('horizon.framework.util.workflow')
    .factory('horizon.framework.util.workflow.service', workflowService);

  workflowService.$inject = [
    'horizon.framework.util.extensible.service'
  ];

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

    angular
      .module('MyModule')
      .factory('myService', myService);

    myService.$inject = ['$q', 'horizon.framework.util.workflow.service'];

    function myService ($q, workflow) {

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
    }
   ```
   */
  function workflowService(extensibleService) {
    return function createWorkflow(spec, decorators) {
      angular.forEach(decorators, function decorate(decorator) {
        decorator(spec);
      });
      extensibleService(spec, spec.steps);
      return spec;
    };
  }

})();
