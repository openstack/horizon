/*
 * (c) Copyright 2015 Hewlett Packard Enterprise Development Company LP
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

(function() {
  'use strict';

  angular
    .module('horizon.dashboard.developer.resource-browser')
    .controller('horizon.dashboard.developer.resource-browser.ResourceBrowserController', ResourceBrowserController);

  ResourceBrowserController.$inject = [
    '$location',
    '$scope',
    'horizon.framework.conf.resource-type-registry.service',
  ];

  /**
   * @ngdoc controller
   * @name horizon.dashboard.developer.resource-browser:ResourceBrowserController
   * @description
   * This controller allows the launching of any actions registered for resource types
   */
  function ResourceBrowserController($location, $scope, registryService) {
    var ctrl = this;
    ctrl.resourceTypes = registryService.resourceTypes;
  }

})();
