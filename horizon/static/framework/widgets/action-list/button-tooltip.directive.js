/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 *
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

  /**
   * @ngdoc directive
   * @name horizon.framework.widgets.action-list.directive:buttonTooltip
   * @element action-list
   * @param {string} buttonTooltip The tooltip message
   * @param {object} btModel Custom tooltip model (optional)
   * @param {string} btPlacement Tooltip placement (optional)
   * @param {string} btDisabled Disable the tooltip (optional)
   * @description
   * The `buttonTooltip` directive provides a tooltip with a general
   * warning message. This directive should be added as an attribute
   * to an action-list element. The content of the tooltip can be
   * configured by providing a template and necessary data.
   *
   * Custom Tooltip Model:
   * ```
   * $scope.tooltipModel = {
   *   data: {
   *     message: 'My custom message',
   *     anotherMessage: 'Another message',
   *     clickMe: function () {
   *       alert('You clicked me');
   *     }
   *   },
   *   templateUrl: path + 'myWarningTooltip.html'
   * }
   * ```
   *
   * @restrict A
   * @scope
   *
   * @example
   * ```
   * <action-list button-tooltip bt-model="tooltipModel">
   *   <action>...</action>
   * </action-list>
   * ```
   */
  angular
    .module('horizon.framework.widgets.action-list')
    .directive('buttonTooltip', buttonTooltip);

  buttonTooltip.$inject = [
    '$compile',
    '$http',
    '$templateCache',
    'horizon.framework.widgets.action-list.tooltipConfig'
  ];

  function buttonTooltip($compile, $http, $templateCache, tooltipConfig) {
    var directive = {
      link: link,
      restrict: 'A',
      scope: {
        btDisabled: '=?',
        btMessage: '=buttonTooltip',
        btModel: '=?',
        btPlacement: '=?'
      }
    };

    return directive;

    function link(scope, element) {
      var tooltip = scope.btModel || {};
      var template = tooltip.template || tooltipConfig.defaultTemplate;
      if (tooltip.templateUrl) {
        $http.get(tooltip.templateUrl, { cache: $templateCache })
          .then(function (response) {
            template = response.data;
          });
      }

      element.on('blur', 'button', btnBlur);
      element.on('mousedown', btnMouseDown);
      element.on('mouseup', btnMouseUp);

      function btnBlur() {
        element.popover('destroy');
      }

      function btnMouseDown() {
        if (!scope.btDisabled) {
          var popoverElt = element.next('.popover');
          if (popoverElt.length) {
            element.popover('destroy');
          } else {
            createTooltip();
          }
          return false;
        }
      }

      function btnMouseUp() {
        if (!scope.btDisabled) {
          element.find('button').first().focus();
        }
      }

      function createTooltip() {
        // Use default message if custom tooltip model or message not available
        var tooltipData = angular.extend({}, tooltip.data);
        tooltipData.message = scope.btMessage || tooltipConfig.defaultMessage.message;

        // Compile the template with custom tooltip model
        var tooltipScope = scope.$new(true);
        angular.extend(tooltipScope, tooltipData);
        tooltipScope.element = element;
        var compiledTemplate = $compile(template)(tooltipScope);
        tooltipScope.$apply();

        var options = {
          content: compiledTemplate,
          html: true,
          placement: scope.btPlacement || 'left',
          trigger: 'manual'
        };

        element.popover(options);
        element.popover('show');
      }
    }
  }
})();
