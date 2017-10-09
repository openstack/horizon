(function () {
  'use strict';

  angular
    .module('horizon.app.core.openstack-service-api')
    .factory('horizon.app.core.openstack-service-api.blazar', blazarAPI);

  blazarAPI.$inject = [
    'horizon.framework.util.http.service',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngdoc service
   * @name blazarAPI
   * @param {Object} apiService
   * @param {Object} toastService
   * @description Provides direct pass through to Blazar
   * @returns {Object} The service
   */
  function blazarAPI(apiService, toastService) {
    var service = {
      reservations: reservations,
    };

    return service;

    /**
     * @name reservations
     * @description
     * Get active reservations.
     *
     * @param {string} params
     * - xxxx
     * Undefined.
     *
     * @param {boolean} suppressError
     * If passed in, this will not show the default error handling
     * (horizon alert).
     * @returns {Object} The result of the API call
     */
    function reservations(params, suppressError) {
      var promise = apiService.get('/api/blazar/reservations/', params);
      return suppressError ? promise : promise.error(function() {
        toastService.add('error', gettext('Unable to get active reservations.'));
      });
    }
  }

}());
