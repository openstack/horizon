/*
 * Copyright 2019 99Cloud Inc.
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
    .module('horizon.framework.util.timezones', [])
    .factory('horizon.framework.util.timezones.service', timeZoneService);

  timeZoneService.$inject = [
    '$q',
    'horizon.framework.util.http.service'
  ];

    /**
     * @ngdoc service
     * @name timeZoneService
     * @param {Object} $q
     * @param {Object} ApiService
     * @description
     * Horizon's AngularJS pages(for example Images and Keypairs) display dates
     * using browser's timezone now. This service get timezone offset from
     * Horizon's Settings and if Timezone is not set under Settings, AngularJS
     * pages will display dates in 'UTC' timezone.
     * @returns {Object} The service
     */

  function timeZoneService($q, ApiService) {
    var service = {
      getTimeZones: getTimeZones,
      getTimeZoneOffset: getTimeZoneOffset
    };

    return service;

      /////////

    function getTimeZones() {
      return ApiService.get('/api/timezones/', {cache: true});
    }

    function getTimeZoneOffset(timezone) {
      var deferred = $q.defer();

      function onTimezonesLoaded(response) {
        var offsetDict = response.data.timezone_dict;
        timezone = timezone || 'UTC';
        deferred.resolve(offsetDict[timezone]);
      }

      function onTimezonesFailure(message) {
        deferred.reject(message);
      }

      service.getTimeZones()
        .then(onTimezonesLoaded, onTimezonesFailure);

      return deferred.promise;
    }
  }
}());
