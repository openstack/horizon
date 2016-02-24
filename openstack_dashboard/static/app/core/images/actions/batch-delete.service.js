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
    .factory('horizon.app.core.images.actions.batch-delete.service', batchDeleteService);

  batchDeleteService.$inject = [
    'horizon.app.core.images.actions.delete-image.service',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.framework.util.i18n.gettext'
  ];

  /**
   * @ngDoc factory
   * @name horizon.app.core.images.actions.batch-delete.service
   *
   * @Description
   * Brings up the delete images confirmation modal dialog.
   * On submit, delete selected images.
   * On cancel, do nothing.
   */
  function batchDeleteService(
    deleteImageService,
    policy,
    gettext
  ) {
    var context = {
      title: gettext('Confirm Delete Images'),
      /* eslint-disable max-len */
      message: gettext('You have selected "%s". Please confirm your selection. Deleted images are not recoverable.'),
      /* eslint-enable max-len */
      submit: gettext('Delete Images'),
      success: gettext('Deleted Images: %s.'),
      error: gettext('Unable to delete Images: %s.')
    };

    var service = {
      initScope: initScope,
      perform: perform,
      allowed: allowed
    };

    return service;

    //////////////

    // include this function in your service
    // if you plan to emit events to the parent controller
    function initScope(newScope) {
      deleteImageService.initScope(newScope, context);
    }

    // delete selected image objects
    function perform(selected) {
      deleteImageService.perform(selected);
    }

    function allowed() {
      return policy.ifAllowed({ rules: [['image', 'delete_image']] });
    }

  } // end of batchDeleteService
})(); // end of IIFE
