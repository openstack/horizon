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
    .module('horizon.app.core.images')
    .controller('ImageDetailController', ImageDetailController);

  ImageDetailController.$inject = [
    'horizon.app.core.images.tableRoute',
    'horizon.app.core.images.resourceType',
    'horizon.app.core.openstack-service-api.glance',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.framework.conf.resource-type-registry.service',
    '$routeParams'
  ];

  function ImageDetailController(
    tableRoute,
    imageResourceTypeCode,
    glanceAPI,
    keystoneAPI,
    registry,
    $routeParams
  ) {
    var ctrl = this;

    ctrl.image = {};
    ctrl.project = {};
    ctrl.hasCustomProperties = false;
    ctrl.tableRoute = tableRoute;
    ctrl.resourceType = registry.getResourceType(imageResourceTypeCode);

    var imageId = $routeParams.imageId;

    init();

    function init() {
      // Load the elements that are used in the overview.
      glanceAPI.getImage(imageId).success(onGetImage);

      ctrl.hasCustomProperties =
        angular.isDefined(ctrl.image) &&
        angular.isDefined(ctrl.image.properties);
    }

    function onGetImage(image) {
      ctrl.image = image;

      ctrl.image.properties = Object.keys(ctrl.image.properties).map(function mapProps(prop) {
        return {name: prop, value: ctrl.image.properties[prop]};
      });
    }
  }

})();
