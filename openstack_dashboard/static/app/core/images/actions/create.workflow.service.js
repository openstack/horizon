/**
 * (c) Copyright 2016 Hewlett-Packard Development Company, L.P.
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
    .factory('horizon.app.core.images.actions.createWorkflow', createWorkflow);

  createWorkflow.$inject = [
    'horizon.app.core.images.basePath',
    'horizon.app.core.workflow.factory',
    'horizon.framework.util.i18n.gettext'
  ];

  /**
   * @ngdoc factory
   * @name horizon.app.core.images.createWorkflow
   * @description A workflow for the create image action.
   */
  function createWorkflow(basePath, workflowService, gettext) {
    var workflow = workflowService({
      title: gettext('Create Image'),
      btnText: { finish: gettext('Create Image') },
      steps: [
        {
          title: gettext('Image Details'),
          templateUrl: basePath + 'steps/create-image/create-image.html',
          helpUrl: basePath + 'steps/create-image/create-image.help.html',
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
