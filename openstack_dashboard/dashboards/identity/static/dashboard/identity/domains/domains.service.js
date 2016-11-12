/*
 * Copyright 2016 NEC Corporation.
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

  angular.module('horizon.dashboard.identity.domains')
    .factory('horizon.dashboard.identity.domains.service', domainService);

  domainService.$inject = [
    '$q',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.app.core.openstack-service-api.settings',
    'horizon.app.core.detailRoute'
  ];

  /*
   * @ngdoc factory
   * @name horizon.dashboard.identity.domains.service
   *
   * @description
   * This service provides functions that are used through the Domains
   * features.  These are primarily used in the module registrations
   * but do not need to be restricted to such use.  Each exposed function
   * is documented below.
   */
  function domainService($q, keystone, policy, settingsService, detailRoute) {
    return {
      getDetailsPath: getDetailsPath,
      getDomainPromise: getDomainPromise,
      listDomains: listDomains
    };

    /*
     * @ngdoc function
     * @name getDetailsPath
     * @param item {Object} - The domain object
     * @description
     * Given an Domain object, returns the relative path to the details
     * view.
     */
    function getDetailsPath(item) {
      return detailRoute + 'OS::Keystone::Domain/' + item.id;
    }

    /*
     * @ngdoc function
     * @name listDomains
     * @description
     * Returns list of domains. This is used in displaying lists of Domains.
     * In this case, we need to modify the API's response by adding a
     * composite value called 'trackBy' to assist the display mechanism
     * when updating rows.
     */
    function listDomains() {
      var defaultDomain = null;
      var KEYSTONE_DEFAULT_DOMAIN = null;

      return $q.all([
        keystone.getDomain('default'),
        settingsService.getSetting('OPENSTACK_KEYSTONE_DEFAULT_DOMAIN')
      ]).then(allowed);

      function allowed(results) {
        defaultDomain = results[0].data;
        KEYSTONE_DEFAULT_DOMAIN = results[1];

        var rules = [['identity', 'identity:list_domains']];
        return policy.ifAllowed({ rules: rules }).then(policySuccess, policyFailed);
      }

      function policySuccess() {
        if (isDefaultDomain()) {
          // In case that a user is cloud admin and context is Keystone default domain.
          return keystone.getDomains().then(getDomainSuccess);
        } else {
          // In case that a user is cloud admin but has a specific domain scope.
          return keystone.getDomain(defaultDomain.id).then(getDomainSuccess);
        }
      }

      function policyFailed() {
        // In case that a user doesn't have a privilege of list_domains.
        return keystone.getDomain(defaultDomain.id).then(getDomainSuccess);
      }

      function getDomainSuccess(response) {
        if (!angular.isArray(response.data.items)) {
          // the result of getDomain is not array.
          response.data.items = [response.data];
        }
        return {data: {items: response.data.items.map(modifyDomain)}};

        function modifyDomain(domain) {
          domain.trackBy = domain.id;
          return domain;
        }
      }

      function isDefaultDomain() {
        return defaultDomain.name === KEYSTONE_DEFAULT_DOMAIN;
      }
    }

    /*
     * @ngdoc function
     * @name getDomainPromise
     * @description
     * Given an id, returns a promise for the domain data.
     */
    function getDomainPromise(identifier) {
      return keystone.getDomain(identifier);
    }
  }

})();
