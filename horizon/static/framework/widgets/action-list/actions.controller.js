/*
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

(function() {
  'use strict';

  angular
    .module('horizon.framework.widgets.action-list')
    .controller('horizon.framework.widgets.action-list.ActionsController', ActionsController);

  ActionsController.$inject = [];

  /**
   * @ngdoc controller
   * @name horizon.framework.widgets.action-list.controller:ActionsController
   * @description
   * This controller provides a shared scope across actions within each usage
   * of the Actions directive. Each generated action will have visibility to
   * functions and variables within this controller.
   *
   */
  function ActionsController() {
    var ctrl = this;
    ctrl.passThroughCallbacks = {};

    ctrl.generateDynamicCallback = generateDynamicCallback;

    /**
     * The Actions service takes care of dynamically adding individual
     * Actions to the HTML so that they are rendered properly. Each individual
     * Action directive in turn generates an HTML button with an ng-click that
     * expects a function named "callback" to be in scope. Due to the multiple
     * layers of AngularJS interpretation we are not able to directly bind
     * each callback function from the Service to the Action scope. Instead,
     * we need to bind the service functions to the Actions scope and provide
     * the Action directive with the reference to the Actions scoped callback.
     *
     * This function generates a unique reference for each Action Service
     * and adds it to the Actions scope. When the user pressed the button,
     * the ng-click will look for the callback variable in Action scope
     * which will actually point to the Service's 'perform' function in
     * the Actions scope.
     *
     * ng-click --> (Action scope) callback --> (Actions scope) callback
     *
     * This basically provides passthrough functionality.
     *
     * @example
     *
     * var actions = [{
     *   service: deleteImageService,
     *   template: {
     *     text: gettext('Delete Image'),
     *     type: 'delete'
     *   }
     * }, {
     *   service: createVolumeService,
     *   template: {
     *     text: gettext('Create Volume')
     *   }
     * }];
     *
     * If both the actions were allowed, the 'passThroughCallbacks'
     * will be
     * {
     *   'actionsCtrl.passThroughCallbacks.callback0': deleteImageService.perform,
     *   'actionsCtrl.passThroughCallbacks.callback1': createVolumeService.perform
     * }
     *
     * @param {function} service the service to call 'perform' when action is performed
     * @param {integer} index unique index of the action
     * @returns {string} the callback name to use
     *
     */
    function generateDynamicCallback(service, index) {
      var dynCallbackName = "callback" + index;
      ctrl.passThroughCallbacks[dynCallbackName] = service.perform;
      return 'actionsCtrl.passThroughCallbacks.' + dynCallbackName;
    }

  }

})();
