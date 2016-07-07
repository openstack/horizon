/**
 * (c) Copyright 2016 Hewlett-Packard Development Company, L.P.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

(function() {
  'use strict';

  /**
   * @ngdoc controller
   * @name horizon.app.core.images.DrawerController
   * @description
   * This is the controller for the images drawer (summary) view.
   * Its primary purpose is to provide the metadata definitions to
   * the template via the ctrl.metadataDefs member.
   */
  angular
    .module('horizon.app.core.images')
    .controller('horizon.app.core.images.DrawerController', controller);

  controller.$inject = [
    'horizon.app.core.openstack-service-api.glance',
    'horizon.app.core.images.resourceType'
  ];

  var metadataDefs;

  function controller(glance, imageResourceType) {
    var ctrl = this;

    ctrl.metadataDefs = metadataDefs;
    if (!ctrl.metadataDefs) {
      applyMetadataDefinitions();
    }

    function applyMetadataDefinitions() {
      glance.getNamespaces({resource_type: imageResourceType}, true)
        .then(function setMetadefs(data) {
          ctrl.metadataDefs = data.data.items;
        });
    }
  }

})();
