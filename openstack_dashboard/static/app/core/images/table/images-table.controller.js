/**
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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
   * @name ImagesTableController
   *
   * @description
   * Controller for the images table.
   * Serves as the focal point for table actions.
   */
  angular
    .module('horizon.app.core.images')
    .controller('imagesTableController', ImagesTableController);

  ImagesTableController.$inject = [
    'horizon.app.core.images.basePath',
    'horizon.app.core.openstack-service-api.glance'
  ];

  function ImagesTableController(basepath, glance) {

    var ctrl = this;
    ctrl.images = [];
    ctrl.imagesSrc = [];
    ctrl.checked = {};
    ctrl.path = basepath + 'table/';

    init();

    ////////////////////////////////

    function init() {
      // if user has permission
      // fetch table data and populate it
      glance.getImages().success(onGetImages);
    }

    function onGetImages(response) {
      ctrl.imagesSrc = response.items;
    }

  }

})();
