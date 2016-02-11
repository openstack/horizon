/**
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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
    .module('horizon.app.core.openstack-service-api')
    .factory('horizon.app.core.openstack-service-api.userSession', userSession);

  userSession.$inject = [
    '$cacheFactory',
    '$q',
    'horizon.app.core.openstack-service-api.keystone'
  ];

  /**
   * @ngdoc service
   * @name horizon.app.core.openstack-service-api.userSession
   * @description
   * Provides cached access to the user session. The cache may be reset
   * at any time by accessing the cache and calling removeAll, which means
   * that the next call to any function in this service will retrieve fresh
   * results after the cache is cleared. This allows programmatic refresh of
   * the cache.
   *
   * The cache in current horizon (Kilo non-single page app) only has a
   * lifetime of the current page. The cache is reloaded every time you change
   * panels. It also happens when you change the region selector at the top
   * of the page, and when you log back in.
   *
   * So, at least for now, this seems to be a reliable way that will
   * make only a single request to get user information for a
   * particular page or modal. Making this a service allows it to be injected
   * and used transparently where needed without making every single use of it
   * pass it through as an argument.
   */
  function userSession($cacheFactory, $q, keystoneAPI) {

    var service = {
      cache: $cacheFactory(
        'horizon.app.core.openstack-service-api.userSession',
        {capacity: 1}
      ),
      get: get,
      isCurrentProject: isCurrentProject
    };

    return service;

    /////////////

    function get() {
      return keystoneAPI.getCurrentUserSession({cache: service.cache}).then(onGetUserSession);
    }

    function onGetUserSession(response) {
      return response.data;
    }

    /*
     * @ngdoc function
     * @name isCurrentProject
     * @description
     * Given a project ID, returns a promise that either resolves or rejects
     * based on whether the user's current project ID matches or doesn't.
     * @example
     * If you have a project ID for a given item and want to execute code if it
     * matches the user's current project and get the result as a promise
     * (so it can be evaluated asynchronously):
     ```js
     userSessionService.isCurrentProject(item.projectId).then(loadId, ignore);
     ```
     */
    function isCurrentProject(projectId) {
      var deferred = $q.defer();

      get().then(onUserSessionGet);

      return deferred.promise;

      function onUserSessionGet(userSession) {
        if (userSession.project_id === projectId) {
          deferred.resolve();
        } else {
          deferred.reject();
        }
      }
    }
  }

}());
