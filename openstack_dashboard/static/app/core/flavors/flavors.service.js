/*
 * (c) Copyright 2016 Hewlett Packard Enterprise Development LP
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
(function() {
  "use strict";

  angular.module('horizon.app.core.flavors')
    .factory('horizon.app.core.flavors.service', flavorsService);

  flavorsService.$inject = [
    'horizon.app.core.openstack-service-api.nova'
  ];

  function flavorsService(nova) {
    return {
      getFlavorsPromise: getFlavorsPromise
    };

    function getFlavorsPromise(params) {
      var fullParams = angular.extend({}, params, {get_extras: true});
      return nova.getFlavors(fullParams);
    }
  }

})();
