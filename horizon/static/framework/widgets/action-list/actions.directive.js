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
   * The item to pass to the callback when using 'row' type.
   * The variable is evaluated and passed as an argument when evaluating 'allowed'.
   * 'item' is not used when row type is 'batch'.
   *
   * @param {function} allowed
   * Returns an array of actions that can be performed on the item(s).
   * When using 'row' type, the current 'item' will be passed to the function.
   * When using 'batch' type, no arguments are provided.
   *
   * This is an array that should contain objects with the following properties:
   * {
   *   template: <template object - described below>,
   *   permissions: <a promise to determine if action is allowed>,
   *   callback: 'callback for the action'
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
   *      2. 'delete-selected' - Delete multiple rows. Only for 'batch' type.
   *      3. 'create' - Create a new entity. Only for 'batch' type.
   *
   *      The styling and binding of the callback is done by the template.
   *
   *   3. text: 'text', actionClasses: 'custom-classes'
   *      This creates a button with the given text.
   *      For custom styling of the button, `actionClasses` can be optionally included.
   *
   *   permissions: is expected to be a promise that resolves
   *   if the action is permitted and is rejected if not. If there are multiple promises that
   *   need to be resolved, you can $q.all to combine multiple promises into a single promise.
   *
   *   callback: is the method to call when the button is clicked.
   *   When using 'row' type, the current 'item' is evaluated and passed to the function.
   *   When using 'batch' type, 'item' is not passed.
   *   When using 'delete-selected' for 'batch' type, all selected rows are passed.
   *
   * @restrict E
   * @scope
   * @example
   *
   * batch:
   *
   * function actions() {
   *   return [{
   *     callback: 'table.batchActions.delete.open',
   *     template: {
   *       type: 'delete-selected',
   *       text: gettext('Delete Images')
   *     },
   *     permissions: policy.ifAllowed({ rules: [['image', 'delete_image']] })
   *     }, {
   *     callback: 'table.batchActions.create.open',
   *     template: {
   *       type: 'create',
   *       text: gettext('Create Image')
   *     },
   *     permissions: policy.ifAllowed({ rules: [['image', 'add_image']] })
   *   }];
   * }
   *
   * ```
   * <actions allowed="actions" type="batch">
   * </actions>
   * ```
   *
   * row:
   *
   * function actions(image) {
   *   return [{
   *     callback: 'table.rowActions.deleteImage.open',
   *     template: {
   *       text: gettext('Delete Image'),
   *       type: 'delete'
   *     },
   *     permissions: imageDeletePermitted(image)
   *   }, {
   *     callback: 'table.rowActions.createVolume.open',
   *     template: {
   *       text: gettext('Create Volume')
   *     },
   *     permissions: createVolumeFromImagePermitted(image)
   *   }];
   * }
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
      template: ''
    };

    return directive;

    function link(scope, element, attrs) {
      var listType = attrs.type;
      var item = attrs.item;
      var service = actionsService({
        scope: scope,
        element: element,
        listType: listType,
        item: item
      });
      var allowedActions = $parse(attrs.allowed)(scope);
      if (listType === 'row') {
        var itemVal = $parse(item)(scope);
        service.renderActions(allowedActions(itemVal));
      } else {
        service.renderActions(allowedActions());
      }
    }
  }
})();
