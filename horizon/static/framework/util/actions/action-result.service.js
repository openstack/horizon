/**
 * (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
 *
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
    .module('horizon.framework.util.actions')
    .factory('horizon.framework.util.actions.action-result.service', factory);

  /**
   * @ngdoc factory
   * @name factory
   * @description
   * The purpose of this service is to create action return values in a
   * common manner, making it easier on consumers of such results. For
   * example, if you perform an action that deletes three items, it may be
   * useful for the action to return information that indicates which three
   * items were deleted.
   *
   * Create a new ActionResult object with:
   * ```
   * var actionResult = actionResultService.getActionResult()
   * ```
   *
   * The ActionResult object collects results under four categories: created,
   * updated, deleted and failed. It has methods for registering results of
   * each of those types:
   * ```
   * actionResult.deleted('OS::Glance::Image', id1);
   * actionResult.updated('OS::Glance::Image', id2)
   *             .deleted('OS::Glance::Image', id3);
   * ```
   *
   * These results are then accessed through the actionResult.result property
   * which has four array properties, one for each category, listing objects
   * with {type:, id:} from the above calls.
   *
   * To use actionResultService in an <actions> directive, you would have
   * your directive register a result-handler:
   * ```
   * <actions allowed="ctrl.itemActions" type="row" item="currInstance"
   *          result-handler="ctrl.actionResultHandler"></actions>
   * ```
   *
   * And then in the perform() method of the action, you would construct
   * the actionResult as above, and return the actionResult.result from
   * perform()'s final promise:
   * ```
   * function performUpdate(item) {
   *   $uibModal.open(updateDialog).result.then(function result() {
   *     return actionResult.updated('OS::Glance::Image', item.id).result;
   *   });
   * }
   * ```
   *
   * The controller's result handler (above, ctrl.actionResultHandler)
   * analyzes that result to figure out what to do.  We want to make this
   * capable of handling actions which may return an immediate result
   * or may return a promise, so in our controller we can use $q.when:
   * ```
   * ctrl.actionResultHandler = function resultHandler(returnValue) {
   *   return $q.when(returnValue, actionSuccessHandler);
   * };
   *
   * function actionSuccessHandler(result) {
   *   // simple logic to just reload any time there are updated results.
   *   if (result.updated.length > 0) {
   *     reloadTheList();
   *   }
   * }
   * ```
   */
  function factory() {

    return {
      getActionResult: getActionResult,
      getIdsOfType: getIdsOfType
    };

    /**
     * Returns an array of ids that match the given resource type (e.g. "OS::Glance::Image")
     *
     * @param items - items to filter
     * @param type - type to filter in, or 'undefined' to match all types)
     * @returns [] - array of ids that match the requested type, or an empty array
     */
    function getIdsOfType(items, type) {
      return items ? items.reduce(typeIdReduce, []) : [];

      function typeIdReduce(accumulator, item) {
        if (angular.isUndefined(type) || item.type === type) {
          accumulator.push(item.id);
        }
        return accumulator;
      }
    }

    function getActionResult() {
      return new ActionResult();
    }

    function ActionResult() {
      this.result = {
        created: [],
        updated: [],
        deleted: [],
        failed: []
      };
      this.created = created;
      this.updated = updated;
      this.deleted = deleted;
      this.failed = failed;

      function created(type, id) {
        this.result.created.push({type: type, id: id});
        return this;
      }

      function updated(type, id) {
        this.result.updated.push({type: type, id: id});
        return this;
      }

      function deleted(type, id) {
        this.result.deleted.push({type: type, id: id});
        return this;
      }

      function failed(type, id) {
        this.result.failed.push({type: type, id: id});
        return this;
      }
    }

  }
})();
