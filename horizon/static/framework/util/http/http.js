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

  /* eslint-disable angular/no-service-method */
  angular
    .module('horizon.framework.util.http', [])
    .service('horizon.framework.util.http.service', ApiService);
  /* eslint-enable angular/no-service-method */

  ApiService.$inject = ['$http', '$window'];

  function ApiService($http, $window) {

    var httpCall = function (method, url, data, config) {
      /* eslint-disable angular/window-service */
      url = $window.WEBROOT + url;
      /* eslint-enable angular/window-service */

      url = url.replace(/\/+/g, '/');

      if (angular.isUndefined(config)) {
        config = {};
      }
      // url and method are always provided
      config.method = method;
      config.url = url;
      if (angular.isDefined(data)) {
        config.data = data;
      }

      return $http(config);
    };

    this.get = function(url, config) {
      return httpCall('GET', url, null, config);
    };

    this.post = function(url, data, config) {
      return httpCall('POST', url, data, config);
    };

    this.patch = function(url, data, config) {
      return httpCall('PATCH', url, data, config);
    };

    this.put = function(url, data, config) {
      return httpCall('PUT', url, data, config);
    };

    // NOTE the deviation from $http.delete which does not have the data param
    this.delete = function (url, data, config) {
      return httpCall('DELETE', url, data, config);
    };
  }
}());
