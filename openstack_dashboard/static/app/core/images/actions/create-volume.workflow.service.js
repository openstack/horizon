/**
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

(function() {
  'use strict';

  angular
    .module('horizon.app.core.images')
    .factory('horizon.app.core.images.actions.createVolumeWorkflow', createVolumeWorkflow);

  createVolumeWorkflow.$inject = [
    'horizon.app.core.images.basePath',
    'horizon.app.core.workflow.factory',
    'horizon.framework.util.i18n.gettext'
  ];

  /**
   * @ngdoc factory
   * @name horizon.app.core.images.createVolumeWorkflow
   * @description A workflow for the create volume action.
   */
  function createVolumeWorkflow(basePath, workflowService, gettext) {
    var workflow = workflowService({
      title: gettext('Create Volume'),
      btnText: { finish: gettext('Create Volume') },
      steps: [
        {
          title: gettext('Volume Details'),
          templateUrl: basePath + 'steps/create-volume/create-volume.html',
          helpUrl: basePath + 'steps/create-volume/create-volume.help.html',
          formName: 'volumeForm'
        }
      ]
    });

    return workflow;
  }

})();
