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
   * @ngdoc overview
   * @ngname horizon.app.core.images
   *
   * @description
   * Provides all of the services and widgets required
   * to support and display images related content.
   */
  angular
    .module('horizon.app.core.images', ['ngRoute', 'horizon.app.core.images.actions'])
    .constant('horizon.app.core.images.events', events())
    .constant('horizon.app.core.images.non_bootable_image_types', ['aki', 'ari'])
    .constant('horizon.app.core.images.validationRules', validationRules())
    .constant('horizon.app.core.images.imageFormats', imageFormats())
    .constant('horizon.app.core.images.resourceType', 'OS::Glance::Image')
    .run(registerImageType)
    .config(config);

  registerImageType.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.app.core.images.resourceType'
  ];

  function registerImageType(registry, imageResourceType) {
    registry.getResourceType(imageResourceType, {
      names: [gettext('Image'), gettext('Images')]
    })
      .setProperty('checksum', {
        label: gettext('Checksum')
      })
      .setProperty('container_format', {
        label: gettext('Container Format')
      })
      .setProperty('created_at', {
        label: gettext('Created At')
      })
      .setProperty('disk_format', {
        label: gettext('Disk Format')
      })
      .setProperty('id', {
        label: gettext('ID')
      })
      .setProperty('members', {
        label: gettext('Members')
      })
      .setProperty('min_disk', {
        label: gettext('Min. Disk')
      })
      .setProperty('min_ram', {
        label: gettext('Min. RAM')
      })
      .setProperty('name', {
        label: gettext('Name')
      })
      .setProperty('owner', {
        label: gettext('Owner')
      })
      .setProperty('protected', {
        label: gettext('Protected')
      })
      .setProperty('size', {
        label: gettext('Size')
      })
      .setProperty('status', {
        label: gettext('Status')
      })
      .setProperty('tags', {
        label: gettext('Tags')
      })
      .setProperty('updated_at', {
        label: gettext('Updated At')
      })
      .setProperty('virtual_size', {
        label: gettext('Virtual Size')
      })
      .setProperty('visibility', {
        label: gettext('Visibility')
      })
      .setProperty('description', {
        label: gettext('Description')
      })
      .setProperty('architecture', {
        label: gettext('Architecture')
      })
      .setProperty('kernel_id', {
        label: gettext('Kernel ID')
      })
      .setProperty('ramdisk_id', {
        label: gettext('Ramdisk ID')
      });
  }

  /**
   * @ngdoc constant
   * @name horizon.app.core.images.validationRules
   * @description constants for use in validation fields
   */
  function validationRules() {
    return {
      integer: /^[0-9]+$/,
      fieldMaxLength: 255
    };
  }

  /**
   * @ngdoc constant
   * @name horizon.app.core.images.imageFormats
   * @description constants for list of image types in dropdowns
   */
  function imageFormats() {
    return {
      iso: gettext('ISO - Optical Disk Image'),
      ova: gettext('OVA - Open Virtual Appliance'),
      qcow2: gettext('QCOW2 - QEMU Emulator'),
      raw: gettext('Raw'),
      vdi: gettext('VDI - Virtual Disk Image'),
      vhd: gettext('VHD - Virtual Hard Disk'),
      vmdk: gettext('VMDK - Virtual Machine Disk'),
      aki: gettext('AKI - Amazon Kernel Image'),
      ami: gettext('AMI - Amazon Machine Image'),
      ari: gettext('ARI - Amazon Ramdisk Image'),
      docker: gettext('Docker')
    };
  }

  /**
   * @ngdoc value
   * @name horizon.app.core.images.events
   * @description a list of events for images
   * @returns {Object} The event object
   */
  function events() {
    return {
      DELETE_SUCCESS: 'horizon.app.core.images.DELETE_SUCCESS',
      VOLUME_CHANGED: 'horizon.app.core.images.VOLUME_CHANGED',
      UPDATE_METADATA_SUCCESS: 'horizon.app.core.images.UPDATE_METADATA_SUCCESS',
      UPDATE_SUCCESS: 'horizon.app.core.images.UPDATE_SUCCESS',
      IMAGE_CHANGED: 'horizon.app.core.images.IMAGE_CHANGED',
      IMAGE_METADATA_CHANGED: 'horizon.app.core.images.IMAGE_METADATA_CHANGED'
    };
  }

  config.$inject = [
    '$provide',
    '$windowProvider',
    '$routeProvider'
  ];

  /**
   * @name config
   * @param {Object} $provide
   * @param {Object} $windowProvider
   * @param {Object} $routeProvider
   * @description Routes used by this module.
   * @returns {undefined} Returns nothing
   */
  function config($provide, $windowProvider, $routeProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'app/core/images/';
    $provide.constant('horizon.app.core.images.basePath', path);
    var tableUrl = path + "table/";
    var projectTableRoute = 'project/ngimages/';
    var detailsUrl = path + "detail/";
    var projectDetailsRoute = 'project/ngimages/details/';

    // Share the routes as constants so that views within the images module
    // can create links to each other.
    $provide.constant('horizon.app.core.images.tableRoute', projectTableRoute);
    $provide.constant('horizon.app.core.images.detailsRoute', projectDetailsRoute);

    $routeProvider
      .when('/' + projectTableRoute, {
        templateUrl: tableUrl + 'images-table.html'
      })
      .when('/' + projectDetailsRoute + ':imageId', {
        templateUrl: detailsUrl + 'image-detail.html'
      });
  }

})();
