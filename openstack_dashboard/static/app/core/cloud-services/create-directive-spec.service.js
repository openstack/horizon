/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

  var fromJson = angular.fromJson;
  var isArray = angular.isArray;

  angular
    .module('horizon.app.core.cloud-services')
    .factory('horizon.app.core.cloud-services.createDirectiveSpec', createDirectiveSpec);

  createDirectiveSpec.$inject = ['horizon.app.core.cloud-services.ifFeaturesEnabled'];

  /**
   * @ngdoc factory
   * @name horizon.app.core.cloud-services:factory:createDirectiveSpec
   * @module horizon.app.core.cloud-services
   * @kind function
   * @description
   *
   * A normalized function that can create a directive specification object
   * based on `serviceName`.
   *
   * @param String serviceName The name of the service, e.g. `novaExtensions`.
   * @param String attrName The name of the attribute in the service.
   * @return Object a directive specification object that can be used to
   * create an angular directive.
   */
  function createDirectiveSpec(ifFeaturesEnabled) {
    return function createDirectiveSpec(serviceName, attrName) {
      var directive = {
        link: link,
        restrict: 'E',
        transclude: true
      };

      return directive;

      /////////////////

      function link(scope, element, attrs, ctrl, transclude) {
        element.addClass('ng-hide');
        var features = fromJson(attrs[attrName]);
        if (isArray(features)) {
          ifFeaturesEnabled(serviceName, features).then(featureEnabled, featureDisabled);
        }

        transclude(scope, function(clone) {
          element.append(clone);
        });

        // if the feature is enabled:
        function featureEnabled() {
          element.removeClass('ng-hide');
        }

        // if the feature is not enabled:
        function featureDisabled() {
          element.remove();
        }
      }

    };
  }

})();
