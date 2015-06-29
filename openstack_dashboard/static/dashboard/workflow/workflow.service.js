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

  /**
   * @ngdoc factory
   * @name hz.dashboard.workflow.factory:hz.dashboard.workflow.factory
   * @module hz.dashboard.workflow
   * @kind function
   * @description
   *
   * Injected dependencies:
   * - workflow {@link horizon.framework.util.workflow.service:workflow `workflow`}
   * - dashboardWorkflowDecorator {@link hz.dashboard.workflow.factory
   *    :hz.dashboard.workflow.decorator `dashboardWorkflowDecorator`}
   *
   * @param {Object} The input workflow specification object
   * @returns {Object} The decorated workflow specification object, the same
   * reference to the input spec object.
   *
   */
  angular
    .module('hz.dashboard.workflow')
    .factory('hz.dashboard.workflow.factory', dashboardWorkflow);

  dashboardWorkflow.$inject = [
    'horizon.framework.util.workflow.service',
    'hz.dashboard.workflow.decorator'
  ];

  /////////////

  function dashboardWorkflow(workflow, dashboardWorkflowDecorator) {
    var decorators = [dashboardWorkflowDecorator];
    return function (spec) {
      return workflow(spec, decorators);
    };
  }

})();
