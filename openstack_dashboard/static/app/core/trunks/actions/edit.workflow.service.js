/*
 * Copyright 2017 Ericsson
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
    .module('horizon.app.core.trunks')
    .factory('horizon.app.core.trunks.actions.editWorkflow', editWorkflow);

  editWorkflow.$inject = [
    'horizon.app.core.trunks.basePath',
    'horizon.app.core.workflow.factory',
    'horizon.framework.util.i18n.gettext'
  ];

  /**
   * @ngdoc factory
   * @name horizon.app.core.trunks.editWorkflow
   * @description A workflow for the edit trunk action.
   */
  function editWorkflow(
      basePath,
      workflowService,
      gettext
  ) {
    var workflow = workflowService({
      title: gettext('Edit Trunk'),
      btnText: {finish: gettext('Edit Trunk')},
      steps: [
        {
          title: gettext('Details'),
          templateUrl: basePath + 'steps/trunk-details.html',
          helpUrl: basePath + 'steps/trunk-details.help.html',
          formName: 'detailsForm'
        },
        {
          title: gettext('Subports'),
          templateUrl: basePath + 'steps/trunk-subports.html',
          helpUrl: basePath + 'steps/trunk-subports.help.html',
          formName: 'subportsForm'
        }
      ]
    });

    return workflow;
  }

})();
