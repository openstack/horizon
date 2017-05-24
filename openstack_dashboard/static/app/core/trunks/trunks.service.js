/**
 * Copyright 2017 Ericsson
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
  "use strict";

  angular.module('horizon.app.core.trunks')
    .factory('horizon.app.core.trunks.service', trunksService);

  trunksService.$inject = [
    'horizon.app.core.openstack-service-api.neutron',
    'horizon.app.core.openstack-service-api.userSession'
  ];

  /*
   * @ngdoc factory
   * @name horizon.app.core.trunks.service
   *
   * @description
   * This service provides functions that are used through the Trunks
   * features.  These are primarily used in the module registrations
   * but do not need to be restricted to such use.  Each exposed function
   * is documented below.
   */
  function trunksService(neutron, userSession) {

    return {
      getTrunksPromise: getTrunksPromise
    };

    /*
     * @ngdoc function
     * @name getTrunksPromise
     * @description
     * Given filter/query parameters, returns a promise for the matching
     * trunks. This is used in displaying lists of Trunks.
     */
    function getTrunksPromise(params) {
      return userSession.get().then(getTrunksForProject);

      function getTrunksForProject(userSession) {
        params.project_id = userSession.project_id;
        return neutron.getTrunks(params);
      }
    }
  }

})();
