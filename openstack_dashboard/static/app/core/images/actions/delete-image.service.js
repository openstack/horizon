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
    .factory('horizon.app.core.images.actions.delete-image.service', deleteImageService);

  deleteImageService.$inject = [
    '$q',
    'horizon.app.core.openstack-service-api.glance',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.framework.util.i18n.gettext',
    'horizon.framework.util.q.extensions',
    'horizon.framework.widgets.modal.deleteModalService',
    'horizon.framework.widgets.toast.service',
    'horizon.app.core.images.events'
  ];

  /**
   * @ngDoc factory
   * @name horizon.app.core.images.actions.delete-image.service
   *
   * @Description
   * Brings up the delete images confirmation modal dialog.

   * On submit, delete given images.
   * On cancel, do nothing.
   */
  function deleteImageService(
    $q,
    glance,
    keystone,
    policy,
    gettext,
    $qExtensions,
    deleteModal,
    toast,
    events
  ) {
    var scope, context;
    var notAllowedMessage = gettext("You are not allowed to delete images: %s");
    var deleteImagePromise = policy.ifAllowed({rules: [['image', 'delete_image']]});
    var userSessionPromise = createUserSessionPromise();

    var service = {
      initScope: initScope,
      allowed: allowed,
      perform: perform
    };

    return service;

    //////////////

    function initScope(newScope, actionContext) {
      scope = newScope;
      context = {
        labels: actionContext,
        successEvent: events.DELETE_SUCCESS
      };
    }

    function perform(images) {
      context.deleteEntity = deleteImage;
      $qExtensions.allSettled(images.map(checkPermission)).then(afterCheck);
    }

    function allowed(image) {
      return $q.all([
        notProtected(image),
        deleteImagePromise,
        ownedByUser(image),
        notDeleted(image)
      ]);
    }

    function checkPermission(image) {
      return {promise: allowed(image), context: image};
    }

    function afterCheck(result) {
      if (result.fail.length > 0) {
        toast.add('error', getMessage(notAllowedMessage, result.fail));
      }
      if (result.pass.length > 0) {
        deleteModal.open(scope, result.pass.map(getEntity), context);
      }
    }

    function createUserSessionPromise() {
      var deferred = $q.defer();
      keystone.getCurrentUserSession().success(onUserSessionGet);
      return deferred.promise;

      function onUserSessionGet(userSession) {
        deferred.resolve(userSession);
      }
    }

    function ownedByUser(image) {
      var deferred = $q.defer();

      userSessionPromise.then(onUserSessionGet);

      return deferred.promise;

      function onUserSessionGet(userSession) {
        if (userSession.project_id === image.owner) {
          deferred.resolve();
        } else {
          deferred.reject();
        }
      }
    }

    function notDeleted(image) {
      return $qExtensions.booleanAsPromise(image.status !== 'deleted');
    }

    function notProtected(image) {
      return $qExtensions.booleanAsPromise(!image.protected);
    }

    function deleteImage(image) {
      return glance.deleteImage(image, true);
    }

    function getMessage(message, entities) {
      return interpolate(message, [entities.map(getName).join(", ")]);
    }

    function getName(result) {
      return getEntity(result).name;
    }

    function getEntity(result) {
      return result.context;
    }
  }
})();
