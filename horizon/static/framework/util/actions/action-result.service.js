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
   * The purpose of this service is to conveniently create meaningful return
   * values from an action. For example, if you perform an action that deletes
   * three items, it may be useful for the action to return information
   * that indicates which three items were deleted.
   *
   * The ActionResult object allows an action's code to easily indicate what
   * items were affected.
   *
   * For example, let's say our action deleted three items.  We would
   * resolve the action's promise by appending three 'deleted' items, then
   * conclude by returning the bare result object.
   * @example
   ```
   return actionResultService.getActionResult()
     .deleted('OS::Glance::Image', id1)
     .deleted('OS::Glance::Image', id2)
     .deleted('OS::Glance::Image', id3)
     .result;
   ```
   * As an example of how this is consumed, imagine a situation where there is
   * a display with a list of instances, each having actions.  A user performs
   * one action, let's say Edit Instance; then after the action completes, the
   * user's expectation is that the list of instances is reloaded.  The
   * controller that is managing that display needs to have a hook into the
   * user's action.  This is achieved through returning a promise from the
   * initiation of the action.  In the case of the actions directive, the
   * promise is handled through assigning a result-handler in the table row
   * markup:
   ```
   <actions allowed="ctrl.itemActions" type="row" item="currInstance"
            result-handler="ctrl.actionResultHandler"></actions>
   ```
   * The controller places a handler (above, ctrl.actionResultHandler) on this
   * promise which, when the promise is resolved, analyzes that resolution
   * to figure out logically what to do.  We want to make this logic simple and
   * also capable of handling 'unknown' actions; that is, we want to generically
   * handle any action that a third-party could add.  The action result
   * feature provides this generic mechanism.  The Edit Instance action would
   * resolve with {updated: [{type: 'OS::Nova::Server', id: 'some-uuid'}]},
   * which then can be handled by the controller as required.  In a controller:
   ```
   ctrl.actionResultHandler = function resultHandler(returnValue) {
     return $q.when(returnValue, actionSuccessHandler);
   };

   function actionSuccessHandler(result) {
     // simple logic to just reload any time there are updated results.
     if (result.updated.length > 0) {
       reloadTheList();
     }
   }
   ```
   * This logic of course should probably be more fine-grained than the example,
   * but this demonstrates the basics of how you use action promises and provide
   * appropriate behaviors.
   */
  function factory() {

    return {
      getActionResult: getActionResult,
      getIdsOfType: getIdsOfType
    };

    // Given a list of objects (items) that each have an 'id' property,
    // return a list of those id values for objects whose 'type' property
    // matches the 'type' parameter.
    // This is a convenience method used for extracting IDs from action
    // result objects.  For example, if you wanted to know the IDs of
    // the deleted images (but didn't want to know about other deleted types),
    // you'd use this function.
    function getIdsOfType(items, type) {
      return items ? items.reduce(typeIdReduce, []) : [];

      function typeIdReduce(accumulator, item) {
        if (item.type === type) {
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
