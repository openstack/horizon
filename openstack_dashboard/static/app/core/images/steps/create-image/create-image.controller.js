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
    'horizon.app.core.openstack-service-api.settings',
    'horizon.app.core.openstack-service-api.policy'
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
    settings,
    policyAPI
  ) {
    var ctrl = this;

    settings.getSettings().then(getConfiguredFormatsAndModes);
    ctrl.validationRules = validationRules;
    ctrl.imageFormats = imageFormats;
    ctrl.diskFormats = [];
    ctrl.prepareUpload = prepareUpload;
    ctrl.apiVersion = 0;

    $scope.stepModels.imageForm = ctrl.image = {
      source_type: '',
      image_url: '',
      data: {},
      is_copying: false,
      protected: false,
      min_disk: 0,
      min_ram: 0,
      container_format: '',
      disk_format: '',
      visibility: 'shared'
    };

    ctrl.uploadProgress = -1;

    ctrl.imageProtectedOptions = [
      { label: gettext('Yes'), value: true },
      { label: gettext('No'), value: false }
    ];

    ctrl.imageCopyOptions = [
      { label: gettext('Yes'), value: true },
      { label: gettext('No'), value: false }
    ];

    ctrl.imageSourceOptions = [];

    ctrl.imageVisibilityOptions = [
      { label: gettext('Private'), value: 'private' },
      { label: gettext('Shared'), value: 'shared'}
    ];

    ctrl.kernelImages = [];
    ctrl.ramdiskImages = [];

    ctrl.setFormats = setFormats;
    ctrl.isLocalFileUpload = isLocalFileUpload;

    init();

    var watchUploadProgress = $scope.$on(events.IMAGE_UPLOAD_PROGRESS, watchImageUpload);

    $scope.$on('$destroy', function() {
      watchUploadProgress();
    });

    ///////////////////////////

    function prepareUpload(file) {
      ctrl.image.data = file;
    }

    function watchImageUpload(event, progress) {
      ctrl.uploadProgress = progress;
    }

    function getConfiguredFormatsAndModes(response) {
      ctrl.apiVersion = response.HORIZON_ACTIVE_IMAGE_VERSION;
      var settingsFormats = response.OPENSTACK_IMAGE_FORMATS;
      var uploadMode = response.HORIZON_IMAGES_UPLOAD_MODE;
      var dupe = angular.copy(imageFormats);
      var imageDefaults = response.CREATE_IMAGE_DEFAULTS;

      angular.forEach(dupe, function stripUnknown(name, key) {
        if (settingsFormats.indexOf(key) === -1) {
          delete dupe[key];
        }
      });
      if (uploadMode !== 'off') {
        var uploadValue = 'file-' + uploadMode;
        ctrl.imageSourceOptions.push({
          label: gettext('File'), value: uploadValue
        });
        ctrl.image.source_type = uploadValue;
      }
      if (ctrl.apiVersion < 2 || response.IMAGES_ALLOW_LOCATION) {
        ctrl.imageSourceOptions.push({ label: gettext('URL'), value: 'url' });
        ctrl.image.source_type = 'url';
      }
      ctrl.imageFormats = dupe;
      if (imageDefaults && imageDefaults.image_visibility === "private") {
        ctrl.image.visibility = "private";
      }
    }

    function isLocalFileUpload() {
      var type = ctrl.image.source_type;
      return (type === 'file-legacy' || type === 'file-direct');
    }

    function init() {
      glance.getImages({paginate: false}).success(onGetImages);
      policyAPI.ifAllowed({rules: [['image', 'communitize_image']]}).then(
        function () {
          ctrl.imageVisibilityOptions.push({ label: gettext('Community'), value: 'community' });
        }
      );
      policyAPI.ifAllowed({rules: [['image', 'publicize_image']]}).then(
        function () {
          ctrl.imageVisibilityOptions.push({ label: gettext('Public'), value: 'public' });
        }
      );
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
