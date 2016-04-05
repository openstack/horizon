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
   * Given a list of details views, provides a tab for each.
   *
   * The descriptor is an object that is provided by the resource type
   * features, typically consisting of an 'identifier' member and other
   * members that are used in conveying basic information about the
   * subject of the details views.
   * @example
   *
   * ```
   * <hz-details details-views="ctrl.myDetailsList" descriptor="item.descriptor"></hz-details>
   * ```
   *
   */
  function hzDetails($window) {
    var directive = {
      restrict: 'E',
      scope: {
        detailsViews: '=detailsViews',
        descriptor: '=descriptor',
        defaultTemplateUrl: '=defaultTemplateUrl'
      },
      templateUrl: $window.STATIC_URL + 'framework/widgets/details/details.html'
    };
    return directive;
  }
})();
