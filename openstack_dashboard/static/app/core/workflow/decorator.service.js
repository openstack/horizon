/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 *    Copyright 2016 IBM Corp.
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
   * A workflow decorator function that looks for the requiredServiceTypes or policy
   * properties on each step in the workflow. If either of these properties exist then
   * the checkReadiness method is added to the step. The checkReadiness method will
   * make sure the necessary OpenStack services are enabled and the policy check passes
   * in order for the step to be displayed.
   *
   * Injected dependencies:
   * - $q
   * - serviceCatalog horizon.app.core.openstack-service-api.serviceCatalog
   * - policy horizon.app.core.openstack-service-api.policy
   *
   * @param {Object} spec The input workflow specification object.
   * @returns {Object} The decorated workflow specification object, the same
   * reference to the input spec object.
   */
  /* eslint-ensable max-len */
  angular
    .module('horizon.app.core.workflow')
    .factory('horizon.app.core.workflow.decorator', dashboardWorkflowDecorator);

  dashboardWorkflowDecorator.$inject = [
    '$q',
    'horizon.app.core.openstack-service-api.serviceCatalog',
    'horizon.app.core.openstack-service-api.policy'
  ];

  /////////////

  function dashboardWorkflowDecorator($q, serviceCatalog, policy) {
    return decorator;

    function decorator(spec) {
      decorate(spec);
      return spec;
    }

    function decorate(spec) {
      forEach(spec.steps, decorateStep);
    }

    function decorateStep(step) {
      var promises = [];
      var types = step.requiredServiceTypes;
      if (types && types.length > 0) {
        promises = promises.concat(types.map(function checkServiceEnabled(type) {
          return serviceCatalog.ifTypeEnabled(type);
        }));
      }
      if (step.policy) {
        promises.push(policy.ifAllowed(step.policy));
      }
      if (promises.length > 0) {
        step.checkReadiness = function () {
          return $q.all(promises);
        };
      }
    }
  }

})();
