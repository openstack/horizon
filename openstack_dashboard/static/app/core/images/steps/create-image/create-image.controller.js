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

  angular
    .module('horizon.app.core.images')
    .controller('horizon.app.core.images.steps.CreateImageController', CreateImageController);

  CreateImageController.$inject = [
    '$scope',
    'horizon.app.core.openstack-service-api.glance',
    'horizon.app.core.images.events',
    'horizon.app.core.images.imageFormats',
    'horizon.app.core.images.validationRules',
    'horizon.app.core.openstack-service-api.settings'
  ];

  /**
   * @ngdoc controller
   * @name horizon.app.core.images.steps.CreateImageController
   * @description
   * This controller is use for creating an image.
   */
  function CreateImageController(
    $scope,
    glance,
    events,
    imageFormats,
    validationRules,
    settings
  ) {
    var ctrl = this;

    settings.getSettings().then(getConfiguredFormats);
    ctrl.validationRules = validationRules;
    ctrl.imageFormats = imageFormats;
    ctrl.diskFormats = [];

    ctrl.image = {
      source_type: 'url',
      image_url: '',
      is_copying: true,
      protected: false,
      min_disk: 0,
      min_ram: 0,
      container_format: '',
      disk_format: '',
      visibility: 'public'
    };

    ctrl.imageProtectedOptions = [
      { label: gettext('Yes'), value: true },
      { label: gettext('No'), value: false }
    ];

    ctrl.imageCopyOptions = [
      { label: gettext('Yes'), value: true },
      { label: gettext('No'), value: false }
    ];

    ctrl.imageVisibilityOptions = [
      { label: gettext('Public'), value: 'public'},
      { label: gettext('Private'), value: 'private' }
    ];

    ctrl.kernelImages = [];
    ctrl.ramdiskImages = [];

    ctrl.setFormats = setFormats;

    init();

    var imageChangedWatcher = $scope.$watchCollection('ctrl.image', watchImageCollection);

    $scope.$on('$destroy', function() {
      imageChangedWatcher();
    });

    ///////////////////////////

    function getConfiguredFormats(response) {
      var settingsFormats = response.OPENSTACK_IMAGE_FORMATS;
      var dupe = angular.copy(imageFormats);
      angular.forEach(dupe, function stripUnknown(name, key) {
        if (settingsFormats.indexOf(key) === -1) {
          delete dupe[key];
        }
      });

      ctrl.imageFormats = dupe;
    }

    // emits new data to parent listeners
    function watchImageCollection(newValue, oldValue) {
      if (newValue !== oldValue) {
        $scope.$emit(events.IMAGE_CHANGED, newValue);
      }
    }

    function init() {
      glance.getImages({paginate: false}).success(onGetImages);
    }

    function onGetImages(response) {
      ctrl.kernelImages = response.items.filter(function(elem) {
        return elem.disk_format === 'aki';
      });

      ctrl.ramdiskImages = response.items.filter(function(elem) {
        return elem.disk_format === 'ari';
      });
    }

    function setFormats() {
      ctrl.image.container_format = 'bare';
      if (['aki', 'ami', 'ari'].indexOf(ctrl.image_format) > -1) {
        ctrl.image.container_format = ctrl.image_format;
      }
      ctrl.image.disk_format = ctrl.image_format;
      if (ctrl.image_format === 'docker') {
        ctrl.image.container_format = 'docker';
        ctrl.image.disk_format = 'raw';
      }
    }
  } // end of controller

})();
