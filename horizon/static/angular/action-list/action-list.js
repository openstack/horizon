(function() {
  'use strict';

  /**
   * @ngdoc overview
   * @name hz.widget.action-list
   * @description
   *
   * # hz.widget.action-list
   *
   * The `actionList` directive supports displaying a set of buttons
   * in a Bootstrap button group or button dropdown (single or split).
   *
   * | Directives                                                      |
   * |-----------------------------------------------------------------|
   * | {@link hz.widget.action-list.directive:actionList `actionList`} |
   * | {@link hz.widget.menu.directive:menu `menu`}                    |
   * | {@link hz.widget.action.directive:action `action`}              |
   *
   */
  angular.module('hz.widget.action-list', [ 'ui.bootstrap' ])

  /**
   * @ngdoc directive
   * @name hz.widget.action-list.directive:actionList
   * @element
   * @description
   * The `actionList` directive is the wrapper for the set of
   * actions to be displayed in a Bootstrap button group or
   * button dropdown.
   *
   * The following directives/elements can be declared within
   * this directive element: action, menu, and notifications.
   * Within the menu directive element, any number of `action`
   * directives elements can be declared.
   *
   * If the action list should be a button dropdown, include
   * `dropdown` as an attribute. Additionally, any attribute
   * directives can be added (i.e. warning-tooltip).
   *
   * Notifications are displayed on the bottom right of the
   * button group. Declare any number of icons to display
   * within the `notifications` element. Use `ng-show` or
   * `ng-hide` to dynamically show/hide the icon. Make sure
   * to declare <notifications> first to ensure the button
   * dropdown border radius will display as expected.
   *
   * If a button dropdown is required, declare the dropdown
   * button with the `button-type` attribute set to
   * 'single-button' or 'split-button' for a single button
   * dropdown or split button dropdown, respectively. See
   * (http://getbootstrap.com/components/#btn-dropdowns).
   * The remaining actions should be declared within the
   * `menu` directive element with the `button-type` set to
   * 'menu-item'. These will be converted to links in the
   * dropdown menu.
   *
   * See the `action` and `menu` directives below for more
   * information.
   *
   * @restrict E
   * @example
   *
   * ```
   * <action-list dropdown>
   *   <notifications>
   *     <span class="fa fa-exclamation" ng-show="disabled"></span>
   *   </notifications>
   *   <action button-type="single-button" action-classes="...">
   *     Actions
   *   </action>
   *   <menu>
   *     <action button-type="menu-item" callback="..." item="...">
   *       <span class="fa fa-pencil"></span> Edit
   *     </action>
   *     <action button-type="menu-item" callback="..." item="...">
   *       <span class="fa fa-times"></span> Delete
   *     </action>
   *   </menu>
   * </action-list>
   * ```
   */
  .directive('actionList', [ 'basePath', function(path) {
      return {
        restrict: 'E',
        link: function (scope, element, attrs, ctrl, transclude) {
          element.addClass('btn-group');
        }
      };
    }
  ])

  /**
   * @ngdoc directive
   * @name hz.widget.action-list.directive:menu
   * @element
   * @description
   * The `menu` directive is the wrapper for the set of
   * actions to be displayed in a dropdown menu in a
   * Bootstrap button dropdown. Actions to be displayed
   * should be declared within this directive element.
   *
   * See the `action` directive below for more information.
   *
   * @restrict E
   * @example
   *
   * ```
   * <menu>
   *   <action button-type="menu-item" callback="..." item="...">
   *     <span class="fa fa-pencil"></span> Edit
   *   </action>
   *   <action button-type="menu-item" callback="..." item="...">
   *     <span class="fa fa-times"></span> Delete
   *   </action>
   * </menu>
   * ```
   */
  .directive('menu', [ 'basePath', function(path) {
    return {
      restrict: 'E',
      templateUrl: path + 'action-list/menu.html',
      transclude: true,
      link: function(scope, element, attrs, ctrl, transclude) {
        var menu = element.find('ul');

        // Append menu items to menu
        transclude(scope, function(clone) {
          menu.append(clone);
        });

        // Don't include directive element since
        // it will misalign component look
        menu.unwrap();
      }
    };
  }])

  /**
   * @ngdoc directive
   * @name hz.widget.action-list.directive:action
   * @element
   * @description
   * The `action` directive represents the actions to be
   * displayed in a Bootstrap button group or button
   * dropdown. Any content within this directive element
   * will be appended to the button or link element.
   *
   * There are 4 button types available to an
   * action (`button-type` attribute):
   *
   * Default: <button>
   * Single: <button> with caret icon, use 'single-button'
   * Split: <button> with caret button, use 'split-button'
   * Menu item: <a> wrapped by <li>, use 'menu-item'
   *
   * Attributes:
   *
   * actionClasses: classes added to button or link
   * callback: function called when button or link clicked
   * disabled: disable/enable button dynamically
   * item: object passed to callback function
   *
   * @restrict E
   * @scope
   * @example
   *
   * ```
   * <action button-type="single-button" action-classes="myClasses">
   *   Actions
   * </action>
   *
   * <action button-type="split-button" callback="edit" disabled="editDisabled">
   *   <span class="fa fa-pencil"></span> Edit
   * </action>
   *
   * <action button-type="menu-item" callback="delete" item="row">
   *   Delete
   * </action>
   * ```
   */
  .directive('action', [ 'basePath', function(path) {
      return {
        restrict: 'E',
        scope: {
          actionClasses: '=?',
          callback: '=?',
          disabled: '=?',
          item: '=?'
        },
        templateUrl: function(element, attrs) {
          // Load the template for the action type
          var buttonType = attrs.buttonType || 'action';
          return path + 'action-list/' + buttonType + '.html';
        },
        transclude: true,
        link: function(scope, element, attrs, ctrl, transclude) {
          // Don't include directive element since
          // it will misalign component look
          element.children().first().unwrap();
        }
      };
    }
  ]);

}());