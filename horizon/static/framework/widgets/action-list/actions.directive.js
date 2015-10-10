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
   * allowedActions: actions allowed that can be displayed
   * actionListType: allow the buttons to be shown as a list or doropdown
   *
   * `allowedActions` is a list of allowed actions on the service.
   * It's an array of objects of the form:
   * { template: {}, permissions: <promise to determine permissions>, callback: 'callback'}
   *
   * `template` is an object that can be
   *
   * {url: 'template.html'} the location of the template for the action button.
   * Use this for complete extensibility and control over what is rendered.
   * The template will be responsible for binding the callback and styling.
   *
   * {type: 'type', item: 'item'} use a known action button type.
   * Currently supported values are 'delete', 'delete-selected' and 'create'.
   * `item` is optional and if provided will be used in the callback.
   * The styling and binding of the callback is done by the template.
   *
   * {text: 'text', item: 'item'} use an unstyled button with given text.
   * `item` is optional and if provided will be used in the callback.
   * The styling of the button will vary per the `actionListType` chosen.
   * For custom styling of the button, `actionClasses` can be included in
   * the template.
   *
   * `permissions` is expected to be a promise that resolves
   * if permitted and is rejected if not.
   * `callback` is the method to call when the button is clicked.
   *
   * `actionListType` can be only be `row` or `batch`
   * `batch` is rendered as buttons, `row` is rendered as dropdown menu.
   *
   * @restrict E
   * @scope
   * @example
   *
   * $scope.actions = [{
   *   template: {
   *     text: gettext('Delete Image'),
   *     type: 'delete',
   *     item: 'image'
   *   },
   *   permissions: policy.ifAllowed({ rules: [['image', 'delete_image']] }),
   *   callback: deleteModalService.open
   *  }, {
   *   template: {
   *     text: gettext('Create Volume'),
   *     item: 'image'
   *   },
   *   permissions: policy.ifAllowed({rules: [['volume', 'volume:create']]}),
   *   callback: createVolumeModalService.open
   *  }, {
   *   template: {
   *     url: basePath + 'actions/my-custom-action.html'
   *   },
   *   permissions: policy.ifAllowed({ rules: [['image', 'custom']] }),
   *   callback: customModalService.open
   * }]
   *
   * ```
   * <actions allowed-actions="actions" action-list-type="row">
   * </actions>
   *
   * <actions allowed-actions="actions" action-list-type="batch">
   * </actions>
   * ```
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
      var listType = attrs.actionListType;
      var allowedActions = $parse(attrs.allowedActions)(scope);

      actionsService({scope: scope, element: element, listType: listType})
        .renderActions(allowedActions);
    }
  }
})();
