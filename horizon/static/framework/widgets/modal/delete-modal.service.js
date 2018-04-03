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
    'horizon.framework.widgets.toast.service',
    'horizon.framework.util.q.extensions'
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
  function deleteModalService($q, simpleModalService, toast, $qExtensions) {
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
     * The second argument is the Entity itself.
     * Note: This callback might need to suppress errors on the
     * alert service.
     *
     * @param {string} context.successEvent
     * The name of the event to emit for the entities that have been deleted successfully.
     * @param {string} context.failedEvent
     * The name of the event to emit when the entities that failed to delete successfully.
     *
     * On submit, delete given entities.
     * On cancel, do nothing.
     *
     * @return {Promise} From the opened modal. Resolves on modal submit,
     * rejects on modal cancel.
     *
     */
    function open(scope, entities, context) {
      var options = {
        title: context.labels.title,
        body: interpolate(context.labels.message, [entities.map(getName).join("\", \"")]),
        submit: context.labels.submit
      };

      return simpleModalService.modal(options).result.then(onModalSubmit);

      function onModalSubmit() {
        return $qExtensions.allSettled(entities.map(deleteEntityPromise)).then(notify);
      }

      function deleteEntityPromise(entity) {
        return {promise: context.deleteEntity(entity.id, entity), context: entity};
      }

      function notify(result) {
        if (result.pass.length > 0) {
          var passEntities = result.pass.map(getEntities);
          scope.$emit(context.successEvent, passEntities.map(getId));
          toast.add('success', getMessage(context.labels.success, passEntities));
        }

        if (result.fail.length > 0) {
          var failEntities = result.fail.map(getEntities);
          scope.$emit(context.failedEvent, failEntities.map(getId));
          toast.add('error', getMessage(context.labels.error, failEntities));
        }
        // Return the passed and failed entities as part of resolving the promise
        return result;
      }
    }

    function getEntities(passResponse) {
      return passResponse.context;
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

  } // end of deleteModalService
})(); // end of IIFE
