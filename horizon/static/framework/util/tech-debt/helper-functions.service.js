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
      loadAngular: loadAngular
    };

    return service;

    /*
     * Compile angular directives in a DOM element that has typically been
     * loaded into the page (the only current use of this is in jQuery
     * modal dialogs).
     */
    function loadAngular(element) {
      $compile(element)($rootScope);
      $rootScope.$apply();
    }
  }
})();
