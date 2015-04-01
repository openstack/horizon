/*
Copyright 2014, Rackspace, US, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
(function () {
  'use strict';
  function KeystoneAPI(apiService) {
    // Users
    this.getUsers = function(params) {
      var config = (params) ? {'params': params} : {};
      return apiService.get('/api/keystone/users/', config)
        .error(function () {
          horizon.alert('error', gettext('Unable to retrieve users'));
        });
    };

    this.createUser = function(newUser) {
      return apiService.post('/api/keystone/users/', newUser)
        .error(function () {
          horizon.alert('error', gettext('Unable to create the user.'));
        });
    };

    this.deleteUsers = function(user_ids) {
      return apiService.delete('/api/keystone/users/', user_ids)
        .error(function () {
          horizon.alert('error', gettext('Unable to delete the users.'));
        });
    };

    /**
    * @name hz.api.keystoneApi.getCurrentUserSession
    * @description
    * Gets the current User Session Information
    * @example
    * {
    * "available_services_regions": [
    *     "RegionOne"
    * ],
    * "domain_id": null,
    * "domain_name": null,
    * "enabled": true,
    * "id": "2138efda19264c64b69551c6b08054c9",
    * "is_superuser": true,
    * "project_id": "53fafe441399439a852d3bd81c22caf6",
    * "project_name": "demo",
    * "roles": [
    *     {
    *         "name": "admin"
    *     }
    * ],
    * "services_region": "RegionOne",
    * "user_domain_id": "default",
    * "user_domain_name": "Default",
    * "username": "admin"
    * }
    */
    this.getCurrentUserSession = function(config) {
      return apiService.get('/api/keystone/user-session/', config)
        .error(function () {
          horizon.alert('error',
            gettext('Unable to retrieve the current user session.'));
        });
    };

    this.getUser = function(user_id) {
      return apiService.get('/api/keystone/users/' + user_id)
        .error(function () {
          horizon.alert('error', gettext('Unable to retrieve the user'));
        });
    };

    this.editUser = function(updatedUser) {
      var url = '/api/keystone/users/' + updatedUser.id;
      return apiService.patch(url, updatedUser)
        .error(function () {
          horizon.alert('error', gettext('Unable to edit the user.'));
        });
    };

    this.deleteUser = function(user_id) {
      return apiService.delete('/api/keystone/users/' + user_id)
        .error(function () {
          horizon.alert('error', gettext('Unable to delete the user.'));
        });
    };

    // Roles
    this.getRoles = function() {
      return apiService.get('/api/keystone/roles/')
        .error(function () {
          horizon.alert('error', gettext('Unable to retrieve role'));
        });
    };

    this.createRole = function(newRole) {
      return apiService.post('/api/keystone/roles/', newRole)
        .error(function () {
          horizon.alert('error', gettext('Unable to create the role.'));
        });
    };

    this.deleteRoles = function(role_ids) {
      return apiService.delete('/api/keystone/roles/', role_ids)
        .error(function () {
          horizon.alert('error', gettext('Unable to delete the roles.'));
        });
    };

    this.getRole = function(role_id) {
      return apiService.get('/api/keystone/roles/' + role_id)
        .error(function () {
          horizon.alert('error', gettext('Unable to retrieve the role'));
        });
    };

    this.editRole = function(updatedRole) {
      var url = '/api/keystone/roles/' + updatedRole.id;
      return apiService.patch(url, updatedRole)
        .error(function () {
          horizon.alert('error', gettext('Unable to edit the role.'));
        });
    };

    this.deleteRole = function(role_id) {
      return apiService.delete('/api/keystone/roles/' + role_id)
        .error(function () {
          horizon.alert('error', gettext('Unable to delete the role.'));
        });
    };

    // Domains
    this.getDomains = function() {
      return apiService.get('/api/keystone/domains/')
        .error(function () {
          horizon.alert('error', gettext('Unable to retrieve domains'));
        });
    };

    this.createDomain = function(newDomain) {
      return apiService.post('/api/keystone/domains/', newDomain)
        .error(function () {
          horizon.alert('error', gettext('Unable to create the domain.'));
        });
    };

    this.deleteDomains = function(domain_ids) {
      return apiService.delete('/api/keystone/domains/', domain_ids)
        .error(function () {
          horizon.alert('error', gettext('Unable to delete the domains.'));
        });
    };

    this.getDomain = function(domain_id) {
      return apiService.get('/api/keystone/domains/' + domain_id)
        .error(function () {
          horizon.alert('error', gettext('Unable to retrieve the domain'));
        });
    };

    this.editDomain = function(updatedDomain) {
      var url = '/api/keystone/domains/' + updatedDomain.id;
      return apiService.patch(url, updatedDomain)
        .error(function () {
          horizon.alert('error', gettext('Unable to edit the domain.'));
        });
    };

    this.deleteDomain = function(domain_id) {
      return apiService.delete('/api/keystone/domains/' + domain_id)
        .error(function () {
          horizon.alert('error', gettext('Unable to delete the domain.'));
        });
    };

    // Projects
    this.getProjects = function(params) {
      var config = (params) ? {'params': params} : {};
      return apiService.get('/api/keystone/projects/', config)
        .error(function () {
          horizon.alert('error', gettext('Unable to retrieve projects'));
        });
    };

    this.createProject = function(newProject) {
      return apiService.post('/api/keystone/projects/', newProject)
        .error(function () {
          horizon.alert('error', gettext('Unable to create the project.'));
        });
    };

    this.deleteProjects = function(project_ids) {
      return apiService.delete('/api/keystone/projects/', project_ids)
        .error(function () {
          horizon.alert('error', gettext('Unable to delete the projects.'));
        });
    };

    this.getProject = function(project_id) {
      return apiService.get('/api/keystone/projects/' + project_id)
        .error(function () {
          horizon.alert('error', gettext('Unable to retrieve the project'));
        });
    };

    this.editProject = function(updatedProject) {
      var url = '/api/keystone/projects/' + updatedProject.id;
      return apiService.patch(url, updatedProject)
        .error(function () {
          horizon.alert('error', gettext('Unable to edit the project.'));
        });
    };

    this.deleteProject = function(project_id) {
      return apiService.delete('/api/keystone/projects/' + project_id)
        .error(function () {
          horizon.alert('error', gettext('Unable to delete the project.'));
        });
    };

    this.grantRole = function(project_id, role_id, user_id) {
      return apiService.delete('/api/keystone/projects/' + project_id + '/' +
                               role_id + '/' + user_id)
        .error(function () {
          horizon.alert('error', gettext('Unable to grant the role.'));
        });
    };

     /**
     * @name hz.api.keyStoneAPI.serviceCatalog
     * @description
     * Returns the service catalog.
     * @param {Object} config
     * See $http config object parameters.
     */
    this.serviceCatalog = function(config) {
      return apiService.get('/api/keystone/svc-catalog/', config)
        .error(function () {
          horizon.alert('error', gettext('Unable to fetch the service catalog.'));
        });
    };
  }

  angular.module('hz.api')
    .service('keystoneAPI', ['apiService', KeystoneAPI]);

   /**
   * @ngdoc service
   * @name hz.api.userSession
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
  function userSession($cacheFactory, keystoneAPI) {

    var service = {};

    service.cache = $cacheFactory('hz.api.userSession', {capacity: 1});

    service.get = function () {
      return keystoneAPI.getCurrentUserSession({cache: service.cache})
        .then(function (response) {
          return response.data;
        }
      );
    };

    return service;
  }

  angular.module('hz.api')
    .factory('userSession', ['$cacheFactory', 'keystoneAPI', userSession]);

  /**
   * @ngdoc service
   * @name hz.api.serviceCatalog
   * @description
   * Provides cached access to the Service Catalog with utilities to help
   * with asynchronous data loading. The cache may be reset at any time
   * by accessing the cache and calling removeAll. The next call to any
   * function will retrieve fresh results.
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
  function serviceCatalog($cacheFactory, $q, keystoneAPI, userSession) {

    var service = {};
    service.cache = $cacheFactory('hz.api.serviceCatalog', {capacity: 1});

     /**
     * @name hz.api.serviceCatalog.get
     * @description
     * Returns the service catalog. This is cached.
     *
     * @example
     *
     ```js
        serviceCatalog.get()
          .then(doSomething, doSomethingElse);
     ```
     */
    service.get = function() {
      return keystoneAPI.serviceCatalog({cache: service.cache})
        .then(function(response){
          return response.data;
        }
      );
    };

    /**
     * @name hz.api.serviceCatalog.ifTypeEnabled
     * @description
     * Checks if the desired service is enabled.  If it is enabled, use the
     * promise returned to execute the desired function.  If it is not enabled,
     * The promise will be rejected.
     *
     * @param {string} desiredType The type of service desired.
     *
     * @example
     * Assume if the network service is enabled, you want to get networks,
     * if it isn't, then you will do something else.
     * Assume getNetworks is a function that hits Neutron.
     * Assume doSomethingElse is a function that does something else if
     * the network service is not enabled (optional)
     *
     ```js
        serviceCatalog.ifTypeEnabled('network')
          .then(getNetworks, doSomethingElse);
     ```
     */
    service.ifTypeEnabled = function (desiredType) {
      var deferred = $q.defer();

      $q.all(
        {
          session: userSession.get(),
          catalog: service.get()
        }
      ).then(
        onDataLoaded,
        onDataFailure
      );

      function onDataLoaded(d) {
        if (typeHasEndpointsInRegion(d.catalog,
                                     desiredType,
                                     d.session.services_region)) {
          deferred.resolve();
        } else {
          deferred.reject(interpolate(
            gettext('Service type is not enabled: %(desiredType)s'),
            {desiredType: desiredType},
            true));
        }
      }

      function onDataFailure() {
        deferred.reject(gettext('Cannot get service catalog from keystone.'));
      }

      return deferred.promise;
    };

    function typeHasEndpointsInRegion(catalog, desiredType, desiredRegion) {
      var matchingSvcs = catalog.filter(function (svc) {
        return svc.type === desiredType;
      });

      // Ignore region for identity. Identity service endpoint
      // should not change for different regions.
      if (desiredType === 'identity' && matchingSvcs.length > 0) {
        return true;
      } else {
        return matchingSvcs.some(function (svc) {
          return svc.endpoints.some(function (endpoint) {
            return getEndpointRegion(endpoint) === desiredRegion;
          });
        });
      }
    }

    /*
    * In Keystone V3, region has been deprecated in favor of
    * region_id.
    *
    * This method provides a way to get region that works for
    * both Keystone V2 and V3.
    */
    function getEndpointRegion(endpoint) {
      return endpoint.region_id || endpoint.region;
    }

    return service;
  }

  angular.module('hz.api')
    .factory('serviceCatalog', ['$cacheFactory',
                                '$q',
                                'keystoneAPI',
                                'userSession',
                                serviceCatalog]);

}());
