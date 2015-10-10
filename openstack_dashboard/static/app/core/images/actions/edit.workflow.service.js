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
    .factory('horizon.app.core.images.actions.editWorkflow', editWorkflow);

  editWorkflow.$inject = [
    'horizon.app.core.images.basePath',
    'horizon.app.core.workflow.factory',
    'horizon.framework.util.i18n.gettext'
  ];

  /**
   * @ngdoc factory
   * @name horizon.app.core.images.editWorkflow
   * @description A workflow for the edit image action.
   */
  function editWorkflow(basePath, workflowService, gettext) {
    var workflow = workflowService({
      title: gettext('Edit Image'),
      btnText: { finish: gettext('Update Image') },
      steps: [
        {
          title: gettext('Image Details'),
          templateUrl: basePath + 'steps/edit-image/edit-image.html',
          helpUrl: basePath + 'steps/edit-image/edit-image.help.html',
          formName: 'imageForm'
        },
        {
          title: gettext('Metadata'),
          templateUrl: basePath + 'steps/update-metadata/update-metadata.html',
          helpUrl: basePath + 'steps/update-metadata/update-metadata.help.html',
          formName: 'updateMetadataForm'
        }
      ]
    });

    return workflow;
  }

})();
