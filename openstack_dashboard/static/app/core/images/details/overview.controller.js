/*
 * (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
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
    .module('horizon.app.core.images')
    .controller('ImageOverviewController', ImageOverviewController);

  ImageOverviewController.$inject = [
    'horizon.app.core.images.resourceType',
    'horizon.framework.conf.resource-type-registry.service',
    '$scope'
  ];

  function ImageOverviewController(
    imageResourceTypeCode,
    registry,
    $scope
  ) {
    var ctrl = this;

    ctrl.image = {};
    ctrl.resourceType = registry.getResourceType(imageResourceTypeCode);

    $scope.context.loadPromise.then(onGetImage);

    function onGetImage(image) {
      ctrl.image = image.data;

      ctrl.image.properties = Object.keys(ctrl.image.properties).map(function mapProps(prop) {
        return {name: prop, value: ctrl.image.properties[prop]};
      });
    }
  }

})();
