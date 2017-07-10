/**
 * Copyright 2014, Rackspace, US, Inc.
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
    .factory('horizon.app.core.openstack-service-api.keystone', keystoneAPI);

  keystoneAPI.$inject = [
    '$q',
    'horizon.app.core.openstack-service-api.settings',
    'horizon.framework.util.http.service',
    'horizon.framework.widgets.toast.service'
  ];

  function keystoneAPI($q, settingAPI, apiService, toastService) {
    var service = {
      getVersion: getVersion,
      getUsers: getUsers,
      createUser: createUser,
      deleteUsers: deleteUsers,
      getCurrentUserSession: getCurrentUserSession,
      getUser: getUser,
      editUser: editUser,
      deleteUser: deleteUser,
      getRoles: getRoles,
      createRole: createRole,
      deleteRoles: deleteRoles,
      getRole: getRole,
      editRole: editRole,
      deleteRole: deleteRole,
      getDefaultDomain: getDefaultDomain,
      getDomains: getDomains,
      createDomain: createDomain,
      deleteDomains: deleteDomains,
      getDomain: getDomain,
      editDomain: editDomain,
      deleteDomain: deleteDomain,
      getProjects: getProjects,
      createProject: createProject,
      deleteProjects: deleteProjects,
      getProject: getProject,
      getProjectName: getProjectName,
      editProject: editProject,
      deleteProject: deleteProject,
      grantRole: grantRole,
      serviceCatalog: serviceCatalog,
      getServices: getServices,
      getGroups: getGroups,
      createGroup: createGroup,
      getGroup: getGroup,
      editGroup: editGroup,
      deleteGroup: deleteGroup,
      deleteGroups: deleteGroups,
      canEditIdentity: canEditIdentity
    };

    return service;

    ///////////

    // Version
    function getVersion() {
      return apiService.get('/api/keystone/version/')
        .error(function () {
          toastService.add('error', gettext('Unable to get the Keystone service version.'));
        });
    }

    // Users
    function getUsers(params) {
      var config = params ? {'params': params} : {};
      return apiService.get('/api/keystone/users/', config)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the users.'));
        });
    }

    function createUser(newUser) {
      return apiService.post('/api/keystone/users/', newUser)
        .error(function () {
          toastService.add('error', gettext('Unable to create the user.'));
        });
    }

    function deleteUsers(userIds) {
      return apiService.delete('/api/keystone/users/', userIds)
        .error(function () {
          toastService.add('error', gettext('Unable to delete the users.'));
        });
    }

    function getServices() {
      return apiService.get('/api/keystone/services/')
        .error(function () {
          toastService.add('error', gettext('Unable to fetch the services.'));
        });
    }

    // Group
    function getGroups() {
      return apiService.get('/api/keystone/groups/')
        .error(function () {
          toastService.add('error', gettext('Unable to fetch the groups.'));
        });
    }

    function createGroup(newGroup) {
      return apiService.post('/api/keystone/groups/', newGroup)
        .error(function () {
          toastService.add('error', gettext('Unable to create the group.'));
        });
    }

    function getGroup(groupId) {
      return apiService.get('/api/keystone/groups/' + groupId)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the group.'));
        });
    }

    function editGroup(updatedGroup) {
      var url = '/api/keystone/groups/' + updatedGroup.id;
      return apiService.patch(url, updatedGroup)
        .error(function () {
          toastService.add('error', gettext('Unable to edit the group.'));
        });
    }

    function deleteGroup(groupId) {
      return apiService.delete('/api/keystone/groups/' + groupId)
        .error(function () {
          toastService.add('error', gettext('Unable to delete the group.'));
        });
    }

    function deleteGroups(groupIds) {
      return apiService.delete('/api/keystone/groups/', groupIds)
        .error(function () {
          toastService.add('error', gettext('Unable to delete the groups.'));
        });
    }

    /**
    * @name getCurrentUserSession
    * @param {Object} config - The configuration for which we want a session
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
    * @returns {Object} The result of the API call
    */
    function getCurrentUserSession(config) {
      return apiService.get('/api/keystone/user-session/', config)
        .error(function () {
          toastService.add('error',
            gettext('Unable to retrieve the current user session.'));
        });
    }

    function getUser(userId) {
      return apiService.get('/api/keystone/users/' + userId)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the user.'));
        });
    }

    function editUser(updatedUser) {
      var url = '/api/keystone/users/' + updatedUser.id;
      return apiService.patch(url, updatedUser)
        .error(function () {
          toastService.add('error', gettext('Unable to edit the user.'));
        });
    }

    function deleteUser(userId) {
      return apiService.delete('/api/keystone/users/' + userId)
        .error(function () {
          toastService.add('error', gettext('Unable to delete the user.'));
        });
    }

    // Roles
    function getRoles() {
      return apiService.get('/api/keystone/roles/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the roles.'));
        });
    }

    function createRole(newRole) {
      return apiService.post('/api/keystone/roles/', newRole)
        .error(function () {
          toastService.add('error', gettext('Unable to create the role.'));
        });
    }

    function deleteRoles(roleIds) {
      return apiService.delete('/api/keystone/roles/', roleIds)
        .error(function () {
          toastService.add('error', gettext('Unable to delete the roles.'));
        });
    }

    function getRole(roleId) {
      return apiService.get('/api/keystone/roles/' + roleId)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the role.'));
        });
    }

    function editRole(updatedRole) {
      var url = '/api/keystone/roles/' + updatedRole.id;
      return apiService.patch(url, updatedRole)
        .error(function () {
          toastService.add('error', gettext('Unable to edit the role.'));
        });
    }

    function deleteRole(roleId) {
      return apiService.delete('/api/keystone/roles/' + roleId)
        .error(function () {
          toastService.add('error', gettext('Unable to delete the role.'));
        });
    }

    // Domains
    function getDefaultDomain() {
      return apiService.get('/api/keystone/default_domain/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the default domain.'));
        });
    }

    function getDomains() {
      return apiService.get('/api/keystone/domains/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the domains.'));
        });
    }

    function createDomain(newDomain) {
      return apiService.post('/api/keystone/domains/', newDomain)
        .error(function () {
          toastService.add('error', gettext('Unable to create the domain.'));
        });
    }

    function deleteDomains(domainIds) {
      return apiService.delete('/api/keystone/domains/', domainIds)
        .error(function () {
          toastService.add('error', gettext('Unable to delete the domains.'));
        });
    }

    function getDomain(domainId) {
      return apiService.get('/api/keystone/domains/' + domainId)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the domain.'));
        });
    }

    function editDomain(updatedDomain) {
      var url = '/api/keystone/domains/' + updatedDomain.id;
      return apiService.patch(url, updatedDomain)
        .error(function () {
          toastService.add('error', gettext('Unable to edit the domain.'));
        });
    }

    function deleteDomain(domainId) {
      return apiService.delete('/api/keystone/domains/' + domainId)
        .error(function () {
          toastService.add('error', gettext('Unable to delete the domain.'));
        });
    }

    // Projects
    function getProjects(params) {
      var config = params ? {'params': params} : {};
      return apiService.get('/api/keystone/projects/', config)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the projects.'));
        });
    }

    function createProject(newProject) {
      return apiService.post('/api/keystone/projects/', newProject)
        .error(function () {
          toastService.add('error', gettext('Unable to create the project.'));
        });
    }

    function deleteProjects(projectIds) {
      return apiService.delete('/api/keystone/projects/', projectIds)
        .error(function () {
          toastService.add('error', gettext('Unable to delete the projects.'));
        });
    }

    function getProject(projectId) {
      return apiService.get('/api/keystone/projects/' + projectId)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the project.'));
        });
    }

    /**
     * @name getProjectName
     * @description
     * Returns the requested project name or id if the project doesn't have a name.
     * @param {string} projectId
     * The project to get
     * @returns {string} The result of the API call
     */
    function getProjectName(projectId) {
      var deferred = $q.defer();

      service.getProject(projectId)
        .then(onSuccess, onFailure);

      function onSuccess(response) {
        deferred.resolve(response.data.name || response.data.id);
      }

      function onFailure(message) {
        deferred.reject(message);
      }

      return deferred.promise;
    }

    function editProject(updatedProject) {
      var url = '/api/keystone/projects/' + updatedProject.id;
      return apiService.patch(url, updatedProject)
        .error(function () {
          toastService.add('error', gettext('Unable to edit the project.'));
        });
    }

    function deleteProject(projectId) {
      return apiService.delete('/api/keystone/projects/' + projectId)
        .error(function () {
          toastService.add('error', gettext('Unable to delete the project.'));
        });
    }

    function grantRole(projectId, roleId, userId) {
      return apiService.put('/api/keystone/projects/' + projectId + '/' +
                               roleId + '/' + userId)
        .error(function () {
          toastService.add('error', gettext('Unable to grant the role.'));
        });
    }

    /**
     * @name canEditIdentity
     * @description
     * Returns the promise for can_edit_* setting in OPENSTACK_KEYSTONE_BACKEND.
     * @returns {object} Deferred promiss
     */
    function canEditIdentity(type) {
      var deferred = $q.defer();
      settingAPI.getSetting('OPENSTACK_KEYSTONE_BACKEND', false).then(success);
      return deferred.promise;

      function success(response) {
        if (response["can_edit_" + type]) {
          deferred.resolve();
        } else {
          deferred.reject();
        }
      }
    }

    /**
     * @name serviceCatalog
     * @description
     * Returns the service catalog.
     * @param {Object} config
     * See $http config object parameters.
     * @returns {Object} The result of the API call
     */
    function serviceCatalog(config) {
      return apiService.get('/api/keystone/svc-catalog/', config)
        .error(function () {
          toastService.add('error', gettext('Unable to fetch the service catalog.'));
        });
    }

  }

}());
