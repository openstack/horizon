/*
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
    .module('horizon.framework.util.tech-debt')
    .factory('horizon.framework.util.tech-debt.helper-functions', helperFunctionsService);

  helperFunctionsService.$inject = ['$rootScope', '$compile'];

  function helperFunctionsService($rootScope, $compile) {
    var service = {
      capitalize: capitalize,
      humanizeNumbers: humanizeNumbers,
      truncate: truncate
    };

    return service;

    function capitalize(string) {
      return string.charAt(0).toUpperCase() + string.slice(1);
    }

    /*
     * Adds commas to any integer or numbers within a string for human display.
     *
     *  Example:
     *  horizon.utils.humanizeNumbers(1234); -> "1,234"
     *  horizon.utils.humanizeNumbers("My Total: 1234"); -> "My Total: 1,234"
     *
     */
    function humanizeNumbers(number) {
      return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    /*
     * Truncate a string at the desired length. Optionally append an ellipsis
     * to the end of the string.
     *
     *  Example:
     *  horizon.utils.truncate("String that is too long.", 18, true); ->
     *  "String that is too&hellip;"
     *
     */
    function truncate(string, size, includeEllipsis) {
      if (string.length > size) {
        if (includeEllipsis) {
          return string.substring(0, (size - 3)) + '&hellip;';
        }

        return string.substring(0, size);
      }

      return string;
    }
  }

})();
