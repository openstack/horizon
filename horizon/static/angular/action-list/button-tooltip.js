(function() {
  'use strict';

  angular.module('hz.widget.action-list')

  /**
   * @ngdoc parameters
   * @name hz.widget.action-list.constant:tooltipConfig
   * @param {string} defaultTemplate Default warning tooltip template
   * @param {string} defaultMessage Default warning tooltip message
   */
  .constant('tooltipConfig', {
    defaultTemplate: '<div>{$ ::message $}</div>',
    defaultMessage: {
      message: gettext('The action cannot be performed. The contents of this row have errors or are missing information.')
    }
  })

  /**
   * @ngdoc directive
   * @name hz.widget.action-list.directive:buttonTooltip
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
   *     clickMe: function() {
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
  .directive('buttonTooltip',
    [ 'basePath', '$compile', '$http', '$templateCache', 'tooltipConfig',
    function(path, $compile, $http, $templateCache, tooltipConfig) {
      return {
        restrict: 'A',
        scope: {
          btMessage: '=buttonTooltip',
          btModel: '=?',
          btPlacement: '=?',
          btDisabled: '=?'
        },
        link: function (scope, element, attrs) {

          var tooltip = scope.btModel || {};
          var template = tooltip.template || tooltipConfig.defaultTemplate;
          if (tooltip.templateUrl) {
            $http.get(tooltip.templateUrl, { cache: $templateCache })
              .then(function(response) {
                template = response.data;
              });
          }

          function createTooltip() {
            // If there is a custom tooltip model, use it
            // Otherwise, get the message or use default message
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

          element.on('mousedown', function(e) {
            if (!scope.btDisabled) {
              var popoverElt = element.next('.popover');
              if (popoverElt.length) {
                element.popover('destroy');
              } else {
                createTooltip();
              }
              return false;
            }
          });

          element.on('mouseup', function() {
            if (!scope.btDisabled) {
              element.find('button').first().focus();
            }
          });

          element.on('blur', 'button', function(e) {
            element.popover('destroy');
          });
        }
      };
    }
  ]);

})();