/*
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
    .factory('horizon.app.core.openstack-service-api.heat', heatAPI);

  heatAPI.$inject = [
    'horizon.framework.util.http.service',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngdoc service
   * @name heatAPI
   * @param {Object} apiService
   * @param {Object} toastService
   * @description Provides direct pass through to Heat with NO abstraction.
   * @returns {Object} The service
   */
  function heatAPI(apiService, toastService) {
    var service = {
      validate: validate,
      getServices: getServices
    };

    return service;

    /**
     * @name validate
     * @description
     * Validate a template.
     *
     * @param {string} params
     * - template_url
     * Specifies the template to validate.
     *
     * @param {boolean} suppressError
     * If passed in, this will not show the default error handling
     * (horizon alert).
     * @returns {Object} The result of the API call
     */
    function validate(params, suppressError) {
      var promise = apiService.post('/api/heat/validate/', params);
      return suppressError ? promise : promise.error(function() {
        toastService.add('error', gettext('Unable to validate the template.'));
      });
    }

    /**
     * @name getServices
     * @description Get the list of heat services.
     *
     * @returns {Object} The listing result is an object with property "services." Each item is
     * a service.
     */
    function getServices() {
      return apiService.get('/api/heat/services/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the heat services.'));
        });
    }
  }

}());
