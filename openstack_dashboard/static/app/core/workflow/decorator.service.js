/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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
(function () {
  'use strict';

  var forEach = angular.forEach;

  /* eslint-disable max-len */
  /**
   * @ngdoc factory
   * @name horizon.app.core.workflow.factory:horizon.app.core.workflow.decorator
   * @module horizon.app.core.workflow
   * @kind function
   * @description
   *
   * A workflow decorator function that adds checkReadiness method to step in
   * the work flow.  checkReadiness function will check if a bunch of certain
   * types of OpenStack services is enabled in the cloud for that step to show
   * on the user interface.
   *
   * Injected dependencies:
   * - $q
   * - serviceCatalog horizon.app.core.openstack-service-api.serviceCatalog
   *
   * @param {Object} spec The input workflow specification object.
   * @returns {Object} The decorated workflow specification object, the same
   * reference to the input spec object.
   *
   * | Factories                                                                                                |
   * |----------------------------------------------------------------------------------------------------------|
   * | {@link horizon.app.core.workflow.factory:horizon.app.core.workflow.decorator `horizon.app.core.workflow.decorator`}  |
   *
   */
  /* eslint-ensable max-len */
  angular
    .module('horizon.app.core.workflow')
    .factory('horizon.app.core.workflow.decorator', dashboardWorkflowDecorator);

  dashboardWorkflowDecorator.$inject = [
    '$q',
    'horizon.app.core.openstack-service-api.serviceCatalog'
  ];

  /////////////

  function dashboardWorkflowDecorator($q, serviceCatalog) {
    return decorator;

    function decorator(spec) {
      decorate(spec);
      return spec;
    }

    function decorate(spec) {
      forEach(spec.steps, decorateStep);
    }

    function decorateStep(step) {
      var types = step.requiredServiceTypes;
      if (types && types.length > 0) {
        step.checkReadiness = function () {
          return $q.all(types.map(function (type) {
            return serviceCatalog.ifTypeEnabled(type);
          }));
        };
      }
    }
  }

})();
