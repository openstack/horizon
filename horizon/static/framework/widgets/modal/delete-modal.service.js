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
    .module('horizon.framework.widgets.modal')
    .factory('horizon.framework.widgets.modal.deleteModalService', deleteModalService);

  deleteModalService.$inject = [
    '$q',
    'horizon.framework.widgets.modal.simple-modal.service',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngDoc factory
   * @name horizon.framework.widgets.modal.deleteModalService
   *
   * @Description
   * Brings up the delete confirmation modal dialog.
   * This provides a reusable modal service for deleting
   * entities. It can be used for deleting single or multiple
   * objects.
   *
   * It requires that the backing API Service allow for
   * suppressing of errors so that success and error messages
   * are shown only once when working with multiple objects.
   *
   * On submit, call the given deleteEntity method
   * and then raise the event.
   * On cancel, do nothing.
   */
  function deleteModalService($q, simpleModalService, toast) {
    var service = {
      open: open
    };

    return service;

    //////////////

    /**
     * @ngDoc method
     * @name horizon.framework.widgets.modal.deleteModalService.open
     *
     * @Description
     * Brings up the delete confirmation modal dialog for the given
     * set of entities.
     *
     * @param {Object} entities
     * The Entities that are to be deleted.
     * Each entity MUST have an ID field. They
     * could also have a name field which if present is
     * used in the confirmation display. If a name
     * is not provided, the ID will be displayed.
     *
     * @param {function} context.deleteEntity
     * The function that should be called to delete each entity.
     * The first argument is the id of the Entity to delete.
     * Note: This callback might need to supressErrors on the alert
     * service.
     *
     * @param {string} context.successEvent
     * The name of the event to emit for the entities that have been deleted successfully.
     * @param {string} context.failedEvent
     * The name of the event to emit when the entities that failed to delete successfully.
     *
     * On submit, delete given entities.
     * On cancel, do nothing.
     */
    function open(scope, entities, context) {
      var options = {
        title: context.labels.title,
        body: interpolate(context.labels.message, [entities.map(getName).join("\", \"")]),
        submit: context.labels.submit
      };

      simpleModalService.modal(options).result.then(onModalSubmit);

      function onModalSubmit() {
        resolveAll(entities.map(deleteEntityPromise)).then(notify);
      }

      function deleteEntityPromise(entity) {
        return {promise: context.deleteEntity(entity.id), entity: entity};
      }

      function notify(result) {
        if (result.pass.length > 0) {
          scope.$emit(context.successEvent, result.pass.map(getId));
          toast.add('success', getMessage(context.labels.success, result.pass));
        }

        if (result.fail.length > 0) {
          scope.$emit(context.failedEvent, result.fail.map(getId));
          toast.add('error', getMessage(context.labels.error, result.fail));
        }
      }
    }

    /**
     * Helper method to get the displayed message
     */
    function getMessage(message, entities) {
      return interpolate(message, [entities.map(getName).join(", ")]);
    }

    /**
     * Helper method to get the name of the entity
     */
    function getName(entity) {
      return entity.name || entity.id;
    }

    /**
     * Helper method to get the id of the entity
     */
    function getId(entity) {
      return entity.id;
    }

    /**
     * Resolve all promises.
     * It asks the backing API Service to suppress errors
     * and collect all entities to display one
     * success and one error message.
     */
    function resolveAll(promiseList) {
      var deferred = $q.defer();
      var passList = [];
      var failList = [];
      var promises = promiseList.map(resolveSingle);

      $q.all(promises).then(onComplete);
      return deferred.promise;

      function resolveSingle(singlePromise) {
        var deferredInner = $q.defer();
        singlePromise.promise.then(success, error);
        return deferredInner.promise;

        function success() {
          passList.push(singlePromise.entity);
          deferredInner.resolve();
        }

        function error() {
          failList.push(singlePromise.entity);
          deferredInner.resolve();
        }
      }

      function onComplete() {
        deferred.resolve({pass: passList, fail: failList});
      }
    }
  } // end of batchDeleteService
})(); // end of IIFE
