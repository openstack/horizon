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
    .directive('hzDrawer', hzDrawer);

  hzDrawer.$inject = [ '$window' ];

  /**
   * @ngdoc directive
   * @name horizon.framework.widgets.details:hzDrawer
   * @description
   * Wraps a drawer display, exposing the given item as "item" on the scope
   * and using the template at the given url.
   * @example
   *
   * ```
   * <hz-drawer item="some.item" template-url="my.url || url.generator()"></hz-drawer>
   * ```
   *
   */
  function hzDrawer($window) {
    var directive = {
      restrict: 'E',
      scope: {
        item: '=item',
        templateUrl: '=templateUrl'
      },
      templateUrl: $window.STATIC_URL + 'framework/widgets/details/drawer.html'
    };
    return directive;
  }
})();
