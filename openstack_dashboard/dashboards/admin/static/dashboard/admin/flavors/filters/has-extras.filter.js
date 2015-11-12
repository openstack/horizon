/**
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

  angular
    .module('horizon.dashboard.admin.flavors')
    .filter('hasExtras', hasExtrasFilter);

  hasExtrasFilter.$inject = [];

  /**
   * @ngdoc filter
   * @name hasExtrasFilter
   * @description
   * If input is defined and has more than one property return 'Yes' else return 'No'
   *
   */
  function hasExtrasFilter() {
    return function check(input) {
      if (input &&
          angular.isObject(input) &&
          !angular.isArray(input) &&
          Object.keys(input).length > 0) {
        return true;
      }

      return false;
    };
  }

})();
