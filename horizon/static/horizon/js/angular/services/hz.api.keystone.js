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
/*global angular,horizon*/
(function () {
  'use strict';
  function KeystoneAPI(apiService) {
    // Users
    this.getUsers = function() {
      return apiService.get('/api/keystone/users/')
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
    this.getProjects = function() {
      return apiService.get('/api/keystone/projects/')
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

    this.serviceCatalog = function() {
      return apiService.get('/api/keystone/svc-catalog/')
        .error(function () {
          horizon.alert('error', gettext('Unable to fetch the service catalog.'));
        });
    };
  }

  angular.module('hz.api')
    .service('keystoneAPI', ['apiService', KeystoneAPI]);
}());
