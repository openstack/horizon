/*
Copyright 2015, Rackspace, US, Inc.

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

  /**
   * @ngdoc service
   * @name hz.api.configAPI
   * @description Provides access to dashboard configuration.
   */
  function ConfigAPI(apiService) {

    /**
     * @name hz.api.configAPI.getUserDefaults
     * @description
     * Get the default user configuration settings.
     *
     * Returns an object with user configuration settings.
     */
    this.getUserDefaults = function() {
      return apiService.get('/api/config/user/')
        .success(function(data) {
          // store config in localStorage
          // should be call only when defaults are needed
          // or when user wants to reset it
          localStorage.user_config = angular.toJson(data);
        })
        .error(function () {
          horizon.alert('error', gettext('Unable to retrieve user configuration.'));
        });
    };

    /**
     * @name hz.api.configAPI.getAdminDefaults
     * @description
     * Get the default admin configuration settings.
     *
     * Returns an object with admin configuration settings.
     */
    this.getAdminDefaults = function(params) {
      return apiService.get('/api/config/admin/')
        .success(function(data) {
          // store this in localStorage
          // should be call once each page load
          localStorage.admin_config = angular.toJson(data);
        })
        .error(function () {
          horizon.alert('error', gettext('Unable to retrieve admin configuration.'));
        });
    };
  }

  // Register it with the API module so that anybody using the
  // API module will have access to the Config APIs.
  angular.module('hz.api')
    .service('configAPI', ['apiService', ConfigAPI]);
}());
