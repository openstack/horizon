/*
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
    'horizon.app.core.openstack-service-api.userSession',
    'horizon.app.core.detailRoute',
    '$location',
    '$window'
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
  function trunksService(
    neutron,
    userSession,
    detailRoute,
    $location,
    $window) {

    return {
      getDetailsPath: getDetailsPath,
      getPortDetailsPath: getPortDetailsPath,
      getTrunksPromise: getTrunksPromise,
      getTrunkPromise: getTrunkPromise
    };

    /*
     * @ngdoc function
     * @name getDetailsPath
     * @param item {Object} - The trunk object
     * @description
     * Given a Trunk object, returns the relative path to the details
     * view.
     */
    function getDetailsPath(item) {
      var detailsPath = detailRoute + 'OS::Neutron::Trunk/' + item.id;
      if ($location.url() === '/admin/trunks') {
        detailsPath = detailsPath + "?nav=/admin/trunks/";
      }
      return detailsPath;
    }

    /*
     * @ngdoc function
     * @name getPortDetailsPath
     * @param item {Object} - the trunk object or the relevant subport details
     * object
     * @description
     * Given a trunk object, returns back url for the trunk's parent port or
     * subport detail page, for example:
     * /project/networks/ports/uuid/detail
     */
    function getPortDetailsPath(item) {
      // Note(lajos Katona): the $location.url() can give back /projct/trunks or
      // in case of calling from ngdetails page
      // /ngdetails/OS::Neutron::Trunk/uuid?nav=%2Fadmin%2Ftrunks%2F
      var isAdminFromLocation = $location.url().indexOf('admin') >= 1;

      var dashboardUrl = isAdminFromLocation ? 'admin' : 'project';
      var webRoot = $window.WEBROOT;
      return webRoot + dashboardUrl + '/networks/ports/' + item.port_id + '/detail';
    }

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
        var locationURLNotAdmin = ($location.url().indexOf('admin') === -1);
        // Note(lajoskatona): To list all trunks in case of
        // the listing is for the Admin panel, check here the
        // location.url.
        // there should be a better way to check for admin or project panel??
        if (locationURLNotAdmin) {
          params.project_id = userSession.project_id;
        } else {
          delete params.project_id;
        }

        return neutron.getTrunks(params).then(addTrackBy);
      }

      // Unless we add a composite 'trackBy' field, hz-resource-table of the
      // trunks panel will not get refreshed after editing a trunk.
      // hz-resource-table needs to be told where to expect this information.
      // See also the track-by attribute of hz-resource-table element in the
      // trunks panel template.
      function addTrackBy(response) {

        return {data: {items: response.data.items.map(function(trunk) {
          trunk.trackBy = [
            trunk.id,
            trunk.revision_number,
            // It is weird but there are trunk updates when the revision number
            // does not increase. Eg. if you only update the description of a
            // trunk. So we also add 'updated_at' to the composite.
            trunk.updated_at.toISOString()
          ].join('/');
          return trunk;
        })}};
      }
    }

    /*
     * @ngdoc function
     * @name getTrunkPromise
     * @description
     * Given an id, returns a promise for the trunk data.
     */
    function getTrunkPromise(identifier) {
      // NOTE(bence romsics): This promise is called from multiple places
      // where error handling should differ. When you edit a trunk from the
      // detail view errors of re-reading the trunk should be shown. But
      // when you delete a trunk from the detail view and the deleted
      // trunk is re-read (that fails of course) you don't want to see an
      // error because of that. Ideally we wouldn't even try to re-read (ie.
      // show) after delete from detail (re-list should be enough).
      return neutron.getTrunk(identifier).catch(getTrunkError);

      function getTrunkError(trunk) {
        // TODO(bence romsics): When you delete a trunk from the details
        // view then it cannot be re-read (of course) and we handle that
        // by window.histoy.back(). This is a workaround and must be deleted
        // as soon as there is a final solution for the promels with ngDetails
        // pages.
        $window.history.back();
        return trunk;
      }
    }
  }

})();
