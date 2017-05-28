/*
 * Copyright 2016 IBM Corp.
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

  angular.module('horizon.dashboard.identity.users')
    .factory('horizon.dashboard.identity.users.service', userService);

  userService.$inject = [
    '$q',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.app.core.detailRoute',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.app.core.openstack-service-api.settings'
  ];

  /*
   * @ngdoc factory
   * @name horizon.dashboard.identity.users.service
   */
  function userService($q, keystone, detailRoute, policy, settings) {
    return {
      getDetailsPath: getDetailsPath,
      getUserPromise: getUserPromise,
      getUsersPromise: getUsersPromise,
      getFilterFirstSettingPromise: getFilterFirstSettingPromise
    };

    /*
     * @ngdoc function
     * @name getDetailsPath
     * @param item {Object} - The user object
     * @description
     * Given an user object, returns the relative path to the details view.
     */
    function getDetailsPath(item) {
      return detailRoute + 'OS::Keystone::User/' + item.id;
    }

    /**
     * @ngdoc function
     * @name getUsersPromise
     * @param params - query params
     * @description
     * Returns a promise for the users data.
     */
    function getUsersPromise(params) {
      var rules = [['identity', 'identity:list_users']];
      // Check whether the user has the privilege of list_users, if so, retrieve
      // all the users, otherwise only retrieve the current login user details.
      return policy.ifAllowed({ rules: rules }).then(policySuccess, policyFailed);

      function policySuccess() {
        return keystone.getUsers(params).then(modifyResponse);
      }

      function policyFailed() {
        // In case that a user doesn't have a privilege of list_users.
        return keystone.getUser('current').then(modifyResponse);
      }

      function modifyResponse(response) {
        if (!angular.isArray(response.data.items)) {
          // the result of getUser is not array.
          response.data.items = [angular.copy(response.data)];
        }
        return {data: {items: response.data.items.map(modifyItem)}};

        function modifyItem(item) {
          item.trackBy = item.id + item.name + item.email + item.project +
            item.description + item.enabled;
          return item;
        }
      }
    }

    /*
     * @ngdoc function
     * @name getUserPromise
     * @description
     * Given an id, returns a promise for the user data.
     * Need to add domain information to user object if v3 supported
     */
    function getUserPromise(identifier) {
      return $q.all([
        keystone.getVersion(),
        keystone.getUser(identifier)
      ]).then(getUserDetails);
    }

    function getUserDetails(response) {
      var version = response[0].data.version;
      var user = response[1];
      // get project name
      if (user.data.default_project_id) {
        keystone.getProject(user.data.default_project_id).then(addProjectName);
      }
      // get domain info if v3 supported
      if (version && version >= 3) {
        return keystone.getDomain(user.data.domain_id).then(modifyResponse);
      } else {
        return user;
      }

      function addProjectName(project) {
        user.data.project_name = project.data.name;
        return user;
      }
      function modifyResponse(domain) {
        user.data.domain_name = domain.data.name;
        return user;
      }
    }

    /**
     * @ngdoc function
     * @name getFilterFirstSettingPromise
     * @description Returns a promise for the FILTER_DATA_FIRST setting
     *
     */
    function getFilterFirstSettingPromise() {
      return settings.getSetting('FILTER_DATA_FIRST', {'identity.users': false})
        .then(resolve);

      function resolve(result) {
        return result['identity.users'];
      }

    }
  }

})();
