/**
 * Copyright 2016 IBM Corp.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
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
    .module('horizon.framework.widgets.table')
    .directive('hzDetailRow', hzDetailRow);

  hzDetailRow.$inject = ['horizon.framework.widgets.basePath',
    '$http',
    '$compile',
    '$parse',
    '$templateCache'];

  /**
   * @ngdoc directive
   * @name horizon.framework.widgets.table.directive:hzDetailRow
   * @description
   * The `hzDetailRow` directive is the detail drawer per each row triggered by
   * the hzExpandDetail. Use this option for customization and complete control over what
   * is rendered. If a custom template is not provided, it will use the template
   * found at hz-detail-row.html. 'config.columns' and 'item' must be provided for the
   * default template to work. See example below.
   *
   * It should ideally be used within the context of the `hz-dynamic-table` directive.
   * The params passed into `hz-dynamic-table` can be used in the custom template,
   * including the 'table' scope.
   *
   * @restrict E
   *
   * @param {object=} templateUrl path to custom html template you want to
   *  place inside the detail drawer (optional)
   *
   * @scope
   * @example
   *
   * ```
   * <tbody>
   *   <tr ng-repeat-start="item in items track by $index">
   *     <td ng-show="config.expand" class="expander">
   *       <span class="fa fa-chevron-right"
   *         hz-expand-detail
   *         duration="200">
   *       </span>
   *     </td>
   *     <td ng-repeat="column in config.columns" class="{$ column.classes $}">
   *       item[column.id]
   *     </td>
   *   </tr>
   *   <tr ng-if="config.expand" ng-repeat-end class="detail-row">
   *     <td class="detail" colspan="100">
   *       <hz-detail-row template-url="config.detailsTemplateUrl">
   *       </hz-detail-row>
   *     </td>
   *   </tr>
   * </tbody>
   *
   * ```
   *
   */
  function hzDetailRow(basePath, $http, $compile, $parse, $templateCache) {

    var directive = {
      restrict: 'E',
      scope: false,
      link: link
    };

    return directive;

    function link(scope, element, attrs) {
      var templateUrl = $parse(attrs.templateUrl)(scope);
      if (angular.isUndefined(templateUrl)) {
        templateUrl = basePath + 'table/hz-detail-row.html';
      }
      $http.get(templateUrl, { cache: $templateCache })
        .then(function(response) {
          var template = response.data;
          element.append($compile(template)(scope));
        });
    }
  }
})();
