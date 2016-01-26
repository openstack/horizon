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
   * @name horizon.app.core.workflow.factory:horizon.app.core.workflow.factory
   * @module horizon.app.core.workflow
   * @kind function
   * @description
   *
   * Injected dependencies:
   * - workflow {@link horizon.framework.util.workflow.service:workflow `workflow`}
   * - dashboardWorkflowDecorator {@link horizon.app.core.workflow.factory
   *    :horizon.app.core.workflow.decorator `dashboardWorkflowDecorator`}
   *
   * @example
   * ```
   * var workflow = workflowService({
   *   title: gettext('Create Volume'),
   *   btnText: { finish: gettext('Create Volume') },
   *   steps: [{
   *     title: gettext('Step 1'),
   *     templateUrl: basePath + 'steps/create-volume/step1.html',
   *     helpUrl: basePath + 'steps/create-volume/step1.help.html',
   *     formName: 'step1Form'
   *   },{
   *     title: gettext('Step 2'),
   *     templateUrl: basePath + 'steps/create-volume/step2.html',
   *     helpUrl: basePath + 'steps/create-volume/step2.help.html',
   *     formName: 'step2Form',
   *     requiredServiceTypes: ['network']
   *   },{
   *     title: gettext('Step 3'),
   *     templateUrl: basePath + 'steps/create-volume/step3.html',
   *     helpUrl: basePath + 'steps/create-volume/step3.help.html',
   *     formName: 'step3Form',
   *     policy: { rules: [['compute', 'os_compute_api:os-scheduler-hints:discoverable']] },
   *     setting: 'LAUNCH_INSTANCE_DEFAULTS.enable_scheduler_hints'
   *   }]
   * });
   * ```
   * For each step, the `requiredServiceTypes` property specifies the service types that must
   * be available in the service catalog for the step to be displayed. The `policy` property
   * specifies the policy check that must pass in order for the step to be displayed. The
   * `setting` property specifies the settings key to check (must be a boolean value) for
   * determining if the step should be displayed. If the key is not found then this will resolve
   * to `true`.
   *
   * @param {Object} The input workflow specification object
   * @returns {Object} The decorated workflow specification object, the same
   * reference to the input spec object.
   *
   */
  angular
    .module('horizon.app.core.workflow')
    .factory('horizon.app.core.workflow.factory', dashboardWorkflow);

  dashboardWorkflow.$inject = [
    'horizon.framework.util.workflow.service',
    'horizon.app.core.workflow.decorator'
  ];

  /////////////

  function dashboardWorkflow(workflow, dashboardWorkflowDecorator) {
    var decorators = [dashboardWorkflowDecorator];
    return function (spec) {
      return workflow(spec, decorators);
    };
  }

})();
