/*
 * Licensed under the Apache License, Version 2.0 (the 'License'); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an 'AS IS' BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */
(function () {
  'use strict';

  angular
    .module('horizon.app.core.openstack-service-api')
    .service('horizon.app.core.openstack-service-api.heat', heatAPI);

  heatAPI.$inject = [
    'horizon.framework.util.http.service',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngdoc service
   * @name horizon.app.core.openstack-service-api.heat
   * @description Provides direct pass through to Heat with NO abstraction.
   */
  function heatAPI(apiService, toastService) {
    var service = {
      validate: validate
    };

    return service;

    /**
     * @name horizon.app.core.openstack-service-api.heat.validate
     * @description
     * Validate a template.
     *
     * The result is an object.
     *
     * @param {string} params.template_url
     * Specifies the template to validate.
     *
     * @param {boolean} suppressError
     * If passed in, this will not show the default error handling
     * (horizon alert).
     */
    function validate(params, suppressError) {
      var promise = apiService.post('/api/heat/validate/', params);
      return suppressError ? promise : promise.error(function() {
        toastService.add('error', gettext('Unable to validate the template.'));
      });
    }

  }

}());
