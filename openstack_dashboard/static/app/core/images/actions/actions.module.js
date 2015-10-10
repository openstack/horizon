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

  /**
   * @ngdoc overview
   * @ngname horizon.app.core.images.actions
   *
   * @description
   * Provides all of the actions for images.
   */
  angular.module('horizon.app.core.images.actions', ['horizon.framework.conf', 'horizon.app.core'])
   .run(registerImageActions);

  registerImageActions.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.app.core.images.actions.edit.service',
    'horizon.app.core.images.actions.create-volume.service',
    'horizon.app.core.images.actions.delete-image.service',
    'horizon.app.core.images.actions.launch-instance.service',
    'horizon.app.core.images.actions.update-metadata.service',
    'horizon.app.core.images.resourceType'
  ];

  function registerImageActions(
    registry,
    editService,
    createVolumeService,
    deleteImageService,
    launchInstanceService,
    updateMetadataService,
    imageResourceTypeCode)
  {
    var imageResourceType = registry.getResourceType(imageResourceTypeCode);
    imageResourceType.itemActions
      .append({
        id: 'launchInstanceService',
        service: launchInstanceService,
        template: {
          text: gettext('Launch')
        }
      })
      .append({
        id: 'createVolumeAction',
        service: createVolumeService,
        template: {
          text: gettext('Create Volume')
        }
      })
      .append({
        id: 'editAction',
        service: editService,
        template: {
          text: gettext('Edit Image')
        }
      })
      .append({
        id: 'updateMetadataService',
        service: updateMetadataService,
        template: {
          text: gettext('Update Metadata')
        }
      })
      .append({
        id: 'deleteImageAction',
        service: deleteImageService,
        template: {
          text: gettext('Delete Image'),
          type: 'delete'
        }
      });

    imageResourceType.batchActions
      .append({
        id: 'batchDeleteImageAction',
        service: deleteImageService,
        template: {
          type: 'delete-selected',
          text: gettext('Delete Images')
        }
      });
  }

})();
