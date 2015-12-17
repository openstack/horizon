/*
 * Copyright 2015 IBM Corp.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
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
    .module('horizon.app.core.cloud-services')
    .directive('hzIfApiVersion', hzIfApiVersion);

  hzIfApiVersion.$inject = [
    '$q',
    'hzPromiseToggleTemplateDirective',
    'horizon.app.core.openstack-service-api.glance',
    'horizon.app.core.openstack-service-api.keystone'
  ];

  /**
   * @ngdoc directive
   * @name horizon.app.core.cloud-services:hzIfApiVersion
   * @module horizon.app.core.cloud-services
   *
   * @description
   * Add this directive to any element containing content which should only be
   * evaluated if the api version satisfies the given condition.
   *
   * In addition, the element and everything contained by it will
   * be removed completely, leaving a simple HTML comment.
   *
   * This is evaluated once per page load. In current horizon, this means it
   * will get re-evaluated with events like the user opening another panel,
   * changing logins, or changing their region.
   *
   * The hz-if-api-version attribute is an object that contains two properties, e.g.
   *    (1) "<api_name>": <version_number>
   *            the API name and the version number to check
   *    (2) "operator": <relational_operator>
   *            evaluate the comparison between the actual and expected api version
   *            number using this operator (optional)
   *
   * @example
   *
   * In the first code example below, if keystone v3 is not enabled, then the
   * div element with hz-if-api-version and all of the elements inside of it will
   * be removed and never evaluated by the angular compiler.
   *
   * Optionally, you may pass in an operator for a simple API version comparison
   * (<=, <, =, >, >=), as well as compound several API version checks.
   *
   *
   ```html
    <div hz-if-api-version='{"keystone": 3}'>
      <!-- ui code here is displayed if keystone version == 3 -->
    </div>

    <div hz-if-api-version='{"keystone": 2, "operator": ">="}'>
      <!-- ui code here is displayed if keystone version >= 2 -->
    </div>

    <div hz-if-api-version='[{"keystone": 2}, {"glance": 2, "operator": ">"}]'>
      <!-- ui code here is displayed if keystone == 2 and glance > 2 -->
    </div>
   ```
   */
  function hzIfApiVersion($q, hzPromiseToggle, glance, keystone) {
    return angular.extend(hzPromiseToggle[0], {
      singlePromiseResolver: ifVersionEnabled,
      name: 'hzIfApiVersion'
    });

    function ifVersionEnabled(expected) {
      var deferred = $q.defer();

      var type = Object.keys(expected)[0];
      var operator = expected[Object.keys(expected)[1]];

      switch (type) {
        case "glance": glance.getVersion().then(onSuccess); break;
        case "keystone": keystone.getVersion().then(onSuccess); break;
      }

      function onSuccess(actual) {
        // if operator is passed in, handle simple comparisons
        // check data types to avoid mishandling bad content
        var actualVersion = actual.data.version;
        var expectedVersion = expected[type];
        var isVersion = false;

        if (operator) {
          if (angular.isNumber(actualVersion) &&
              angular.isNumber(expectedVersion) &&
              ["<=", "<", "==", ">", ">="].indexOf(operator) > -1) {
            var expr = actualVersion + operator + expectedVersion;
            /*eslint-disable no-eval */
            isVersion = eval(expr);
            /*eslint-enable no-eval */
          }
        } else {
          if (angular.equals(actualVersion, expectedVersion)) {
            isVersion = true;
          }
        }

        if (isVersion) {
          deferred.resolve();
        } else {
          deferred.reject();
        }
      }
      return deferred.promise;
    }
  }

})();
