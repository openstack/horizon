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
(function () {
  'use strict';

  angular
    .module('horizon.framework.widgets.action-list')
    .directive('actions', actions);

  actions.$inject = [
    '$parse',
    'horizon.framework.widgets.action-list.actions.service'
  ];

  /**
   * @ngdoc directive
   * @name horizon.framework.widgets.action-list.directive:actions
   * @element
   * @description
   * The `actions` directive represents the actions to be
   * displayed in a Bootstrap button group or button
   * dropdown.
   *
   *
   * Attributes:
   *
   * @param {string} type
   * Type can be only be 'row' or 'batch'.
   * 'batch' actions are rendered as a button group, 'row' is rendered as a button dropdown menu.
   * 'batch' actions are typically used for actions across multiple items while
   * 'row' actions are used per item.
   *
   * @param {string=} item
   * The item to pass to the 'service' when using 'row' type.
   *
   * @param {function} allowed
   * Returns an array of actions that can be performed on the item(s).
   *
   * This is an array that should contain objects with the following properties:
   * {
   *   template: <template object - described below>,
   *   service: <service to use - described below>
   * }
   *
   *   template: is an object that can be any of
   *   1. url: <full_path_to_template.html>
   *      This specifies the location of the template for the action button.
   *      Use this for complete extensibility and control over what is rendered.
   *      The template will be responsible for binding the callback and styling the button.
   *
   *   2. type: '<action_button_type>'
   *      This uses a known action button type.
   *      Currently supported values are
   *      1. 'delete' - Delete a single row. Only for 'row' type.
   *      2. 'danger' - For marking an Action as dangerous. Only for 'row' type.
   *      3. 'delete-selected' - Delete multiple rows. Only for 'batch' type.
   *      4. 'create' - Create a new entity. Only for 'batch' type.
   *
   *      The styling and binding of the callback is done by the template.
   *
   *   3. text: 'text', actionClasses: 'custom-classes'
   *      This creates a button with the given text.
   *      For custom styling of the button, `actionClasses` can be optionally included.
   *
   *   service: is the service expected to have two functions
   *   1. allowed: is expected to return a promise that resolves
   *      if the action is permitted and is rejected if not. If there are multiple promises that
   *      need to be resolved, you can $q.all to combine multiple promises into a single promise.
   *      When using 'row' type, the current 'item' will be passed to the function.
   *      When using 'batch' type, no arguments are provided.
   *   2. perform: is what gets called when the button is clicked.
   *      When using 'row' type, the current 'item' is evaluated and passed to the function.
   *      When using 'batch' type, 'item' is not passed.
   *      When using 'delete-selected' for 'batch' type, all selected rows are passed.
   *
   * @restrict E
   * @scope
   * @example
   *
   * batch:
   *
   * Create the services that will implement the actions.
   * Each service must have an allowed function and a perform function.
   *
   * var batchDeleteService = {
   *   allowed: function() {
   *     return policy.ifAllowed({ rules: [['image', 'delete_image']] });
   *   },
   *   perform: function(images) {
   *     images.forEach(function(image){
   *       glanceAPI.deleteImage(image.id);
   *     });
   *   }
   * };
   *
   * var createService = {
   *   allowed: function() {
   *     return policy.ifAllowed({ rules: [['image', 'add_image']] });
   *   },
   *   perform: function() {
   *     //open the modal to create
   *   }
   * };
   *
   * Then create the Service to use in the HTML which lists
   * all allowed actions with the templates to use.
   *
   * function actions() {
   *   return [{
   *     template: {
   *       type: 'delete-selected',
   *       text: gettext('Delete Images')
   *     },
   *     service: batchDeleteService
   *     }, {
   *     template: {
   *       type: 'create',
   *       text: gettext('Create Image')
   *     },
   *     service: createService
   *   }];
   * }
   *
   * Finally, in your HTML, reference the "actions" function and pass
   * in the list of actions that will be allowed.
   *
   * ```
   * <actions allowed="actions" type="batch">
   * </actions>
   * ```
   *
   * row:
   *
   * Create the services that will implement the actions.
   * Each service must have an allowed function and a perform function.
   *
   * var deleteService = {
   *   allowed: function(image) {
   *     return $q.all([
   *       notProtected(image),
   *       policy.ifAllowed({ rules: [['image', 'delete_image']] }),
   *       ownedByUser(image),
   *       notDeleted(image)
   *     ]);
   *   },
   *   perform: function(image) {
   *     glanceAPI.deleteImage(image.id);
   *   }
   * };
   *
   * var createVolumeService = {
   *   allowed: function(image) {
   *     return createVolumeFromImagePermitted(image);
   *   },
   *   perform: function(image) {
   *     //open the modal to create volume
   *   }
   * };
   *
   * Then create the Service to use in the HTML which lists
   * all allowed actions with the templates to use.
   *
   * function actions(image) {
   *   return [{
   *     template: {
   *       text: gettext('Delete Image'),
   *       type: 'delete'
   *     },
   *     service: deleteService
   *   }, {
   *     template: {
   *       text: gettext('Create Volume')
   *     },
   *     service: createVolumeService
   *   }];
   * }
   *
   * Finally, in your HTML, reference the "actions" function and pass
   * in the list of actions that will be allowed.
   *
   * ```
   * <actions allowed="actions" type="row" item="image">
   * </actions>
   *
   * ```
   *
   */
  function actions(
    $parse,
    actionsService
  ) {
    var directive = {
      link: link,
      restrict: 'E',
      scope: true,
      controller: 'horizon.framework.widgets.action-list.ActionsController as actionsCtrl'
    };

    return directive;

    function link(scope, element, attrs, actionsController) {
      var listType = attrs.type;
      var item = attrs.item;
      var allowedActions = $parse(attrs.allowed)(scope)();

      var service = actionsService({
        scope: scope,
        element: element,
        ctrl: actionsController,
        listType: listType,
        item: item
      });

      service.renderActions(allowedActions);
    }
  }
})();
