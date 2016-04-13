/*
 *
 * Licensed under the Apache License, Version 2.0 (the 'License');
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an 'AS IS' BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function() {
  "use strict";

  angular
    .module('horizon.framework.widgets.details')
    .controller('RoutedDetailsViewController', controller);

  controller.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    '$routeParams'
  ];

  function controller(
    registry,
    $routeParams
  ) {
    var ctrl = this;

    ctrl.resourceType = registry.getResourceType($routeParams.type);
    ctrl.descriptor = ctrl.resourceType.parsePath($routeParams.path);
    ctrl.descriptor.loadPromise = ctrl.resourceType.load(ctrl.descriptor.identifier);
    ctrl.descriptor.loadPromise.then(function loadData(response) {
      ctrl.itemData = response.data;
      ctrl.itemName = ctrl.resourceType.itemName(response.data);
    });
    ctrl.defaultTemplateUrl = registry.getDefaultDetailsTemplateUrl();
  }

})();
