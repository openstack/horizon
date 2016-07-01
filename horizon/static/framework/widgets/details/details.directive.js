/*
 * (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
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
    .module('horizon.framework.widgets.details')
    .directive('hzDetails', hzDetails);

  hzDetails.$inject = ['$window'];

  /**
   * @ngdoc directive
   * @name horizon.framework.widgets.details:hzDetails
   * @description
   * Given a list of details views, provides a tab for each if more than one;
   * show a single view without tabs if only one; and if none then display
   * the default details view.
   *
   * The 'context' is an object that is provided by the resource type
   * features, consisting of an 'identifier' member and a 'loadPromise'
   * that are used in conveying basic information about the subject of the
   * details views.
   * @example
   *
   * ```
   * js:
   * ctrl.context = {
   *   identifier: 'some-id',
   *   loadPromise: imageResourceType.load('some-id')
   * };
   * ctrl.defaultTemplateUrl = '/full/path/to/some/fallthough/template.html'
   *
   * markup:
   * <hz-details
   *   views="ctrl.resourceType.detailsViews"
   *   context="ctrl.context"
   *   default-template-url="ctrl.defaultTemplateUrl"
   * ></hz-details>
   * ```
   *
   * The views array should have elements with the properties:
   *
   *   name: a label for the view
   *   template: the template to use in rendering the view
   *
   * This is not an exhaustive list; your template (default or otherwise)
   * may use additional properties.
   */
  function hzDetails($window) {
    var directive = {
      restrict: 'E',
      scope: {
        views: '=',
        context: '=',
        defaultTemplateUrl: '='
      },
      templateUrl: $window.STATIC_URL + 'framework/widgets/details/details.html'
    };
    return directive;
  }
})();
