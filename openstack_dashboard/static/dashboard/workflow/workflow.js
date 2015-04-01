(function () {
  'use strict';

  var forEach = angular.forEach;

  /**
   * @ngdoc overview
   * @name hz.dashboard.workflow
   * @description
   *
   * # hz.dashboard.workflow
   *
   * This module provides utility function factory `dashboardWorkflow` and
   * `dashboardWorkflowDecorator`.
   *
   * | Factories                                                                                      |
   * |------------------------------------------------------------------------------------------------|
   * | {@link hz.dashboard.workflow.factory:dashboardWorkflowDecorator `dashboardWorkflowDecorator`}  |
   *
   */
  angular.module('hz.dashboard.workflow', [])

    /**
     * @ngdoc factory
     * @name hz.dashboard.workflow.factory:dashboardWorkflowDecorator
     * @module hz.dashboard.workflow
     * @kind function
     * @description
     *
     * A workflow decorator function that adds checkReadiness method to step in
     * the work flow.  checkReadiness function will check is a bunch of certain
     * types of OpenStack services is enabled in the cloud for that step to show
     * on the user interface.
     *
     * Injected dependencies:
     * - $q
     * - serviceCatalog hz.api.serviceCatalog
     *
     * @param {Object} spec The input workflow specification object.
     * @returns {Object} The decorated workflow specification object, the same
     * reference to the input spec object.
     *
     * | Factories                                                                                      |
     * |------------------------------------------------------------------------------------------------|
     * | {@link hz.dashboard.workflow.factory:dashboardWorkflowDecorator `dashboardWorkflowDecorator`}  |
     *
     */

    .factory('dashboardWorkflowDecorator', ['$q', 'serviceCatalog',

      function ($q, serviceCatalog) {

        function decorate(spec) {
          forEach(spec.steps, function (step) {
            var types = step.requiredServiceTypes;
            if (types && types.length > 0) {
              step.checkReadiness = function () {
                return $q.all(types.map(function (type) {
                  return serviceCatalog.ifTypeEnabled(type);
                }));
              };
            }
          });
        }

        return function (spec) {
          decorate(spec);
          return spec;
        };
      }
    ])

    /**
     * @ngdoc factory
     * @name hz.dashboard.workflow.factory:dashboardWorkflow
     * @module hz.dashboard.workflow
     * @kind function
     * @description
     *
     * Injected dependencies:
     * - workflow {@link hz.framework.workflow.factory:workflow `workflow`}
     * - dashboardWorkflowDecorator {@link hz.dashboard.workflow.factory
     *    :dashboardWorkflowDecorator `dashboardWorkflowDecorator`}
     *
     * @param {Object} The input workflow specification object
     *
     * @returns {Object} The decorated workflow specification object, the same
     * reference to the input spec object.
     *
     * | Factories                                                                    |
     * |------------------------------------------------------------------------------|
     * | {@link hz.dashboard.workflow.factory:dashboardWorkflow `dashboardWorkflow`}  |
     *
     */

    .factory('dashboardWorkflow', [
      'workflow',
      'dashboardWorkflowDecorator',
      function (workflow, dashboardWorkflowDecorator) {
        var decorators = [dashboardWorkflowDecorator];
        return function (spec) {
          return workflow(spec, decorators);
        };
      }
    ]);

})();
