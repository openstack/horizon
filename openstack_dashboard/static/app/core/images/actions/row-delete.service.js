/**
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use self file except in compliance with the License. You may obtain
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
    .factory('horizon.app.core.images.actions.row-delete.service', deleteService);

  deleteService.$inject = [
    'horizon.app.core.images.actions.delete-image.service',
    'horizon.framework.util.i18n.gettext'
  ];

  /**
   * @ngDoc factory
   * @name horizon.app.core.images.actions.row-delete.service
   *
   * @Description
   * Brings up the delete image confirmation modal dialog.
   * On submit, delete selected image.
   * On cancel, do nothing.
   */
  function deleteService(deleteImageService, gettext) {

    var context = {
      title: gettext('Confirm Delete Image'),
      /* eslint-disable max-len */
      message: gettext('You have selected "%s". Please confirm your selection. Deleted images are not recoverable.'),
      /* eslint-enable max-len */
      submit: gettext('Delete Image'),
      success: gettext('Deleted Image: %s.'),
      error: gettext('Unable to delete Image: %s.')
    };

    var service = {
      initScope: initScope,
      perform: perform,
      allowed: deleteImageService.allowed
    };

    return service;

    //////////////

    // include this function in your service
    // if you plan to emit events to the parent controller
    function initScope(newScope) {
      deleteImageService.initScope(newScope, context);
    }

    // delete selected image
    function perform(image) {
      deleteImageService.perform([image]);
    }

  } // end of deleteService
})(); // end of IIFE
