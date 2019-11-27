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
    .module('horizon.app.core.images', [
      'ngRoute',
      'horizon.app.core.images.actions',
      'horizon.app.core.images.details'
    ])
    .constant('horizon.app.core.images.events', events())
    .constant('horizon.app.core.images.non_bootable_image_types', ['aki', 'ari'])
    .constant('horizon.app.core.images.validationRules', validationRules())
    .constant('horizon.app.core.images.imageFormats', imageFormats())
    .constant('horizon.app.core.images.resourceType', 'OS::Glance::Image')
    .constant('horizon.app.core.images.statuses', {
      'active': gettext('Active'),
      'saving': gettext('Saving'),
      'queued': gettext('Queued'),
      'pending_delete': gettext('Pending Delete'),
      'killed': gettext('Killed'),
      'deactivated': gettext('Deactivated'),
      'deleted': gettext('Deleted')
    })
    .constant('horizon.app.core.images.transitional-statuses', [
      "saving",
      "queued",
      "pending_delete"
    ])
    .run(run)
    .config(config);

  run.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.app.core.images.basePath',
    'horizon.app.core.images.service',
    'horizon.app.core.images.statuses',
    'horizon.app.core.images.resourceType',
    'horizon.framework.util.filters.$memoize',
    'horizon.app.core.openstack-service-api.keystone'
  ];

  function run(registry,
               basePath,
               imagesService,
               statuses,
               imageResourceType,
               $memoize,
               keystone) {
    registry.getResourceType(imageResourceType)
      .setNames('Image', 'Images', ngettext('Image', 'Images', 1))
      .setSummaryTemplateUrl(basePath + 'details/drawer.html')
      .setDefaultIndexUrl('/project/images/')
      .setItemInTransitionFunction(imagesService.isInTransition)
      .setProperties(imageProperties(imagesService, statuses))
      .setListFunction(imagesService.getImagesPromise)
      .setNeedsFilterFirstFunction(imagesService.getFilterFirstSettingPromise)
      .tableColumns
      .append({
        id: 'owner',
        priority: 1,
        filters: [$memoize(keystone.getProjectName)],
        policies: [{rules: [['identity', 'identity:get_project']]}]
      })
      .append({
        id: 'name',
        priority: 1,
        sortDefault: true,
        classes: "word-wrap",
        urlFunction: imagesService.getDetailsPath
      })
      .append({
        id: 'type',
        priority: 1
      })
      .append({
        id: 'status',
        priority: 1,
        itemInTransitionFunction: imagesService.isInTransition
      })
      .append({
        id: 'visibility',
        priority: 1
      })
      .append({
        id: 'protected',
        priority: 1
      })
      .append({
        id: 'disk_format',
        priority: 2
      })
      .append({
        id: 'size',
        priority: 2
      });

    registry.getResourceType(imageResourceType).filterFacets
      .append({
        label: gettext('Name'),
        name: 'name',
        isServer: true,
        singleton: true,
        persistent: true
      })
      .append({
        label: gettext('Status'),
        name: 'status',
        isServer: true,
        singleton: true,
        options: [
          {label: gettext('Active'), key: 'active'},
          {label: gettext('Saving'), key: 'saving'},
          {label: gettext('Queued'), key: 'queued'},
          {label: gettext('Pending Delete'), key: 'pending_delete'},
          {label: gettext('Killed'), key: 'killed'},
          {label: gettext('Deactivated'), key: 'deactivated'},
          {label: gettext('Deleted'), key: 'deleted'}
        ]
      })
      .append({
        label: gettext('Visibility'),
        name: 'visibility',
        isServer: true,
        singleton: true,
        options: [
          {label: gettext('Public'), key: 'public'},
          {label: gettext('Private'), key: 'private'},
          {label: gettext('Shared With Project'), key: 'shared'},
          {label: gettext('Community'), key: 'community'}
        ]
      })
      .append({
        label: gettext('Protected'),
        name: 'protected',
        isServer: true,
        singleton: true,
        options: [
          {label: gettext('Yes'), key: 'true'},
          {label: gettext('No'), key: 'false'}
        ]
      })
      .append({
        label: gettext('Format'),
        name: 'disk_format',
        isServer: true,
        singleton: true,
        options: [
          {label: gettext('AKI'), key: 'aki'},
          {label: gettext('AMI'), key: 'ami'},
          {label: gettext('ARI'), key: 'ari'},
          {label: gettext('Docker'), key: 'docker'},
          {label: gettext('ISO'), key: 'iso'},
          {label: gettext('OVA'), key: 'ova'},
          {label: gettext('PLOOP'), key: 'ploop'},
          {label: gettext('QCOW2'), key: 'qcow2'},
          {label: gettext('Raw'), key: 'raw'},
          {label: gettext('VDI'), key: 'vdi'},
          {label: gettext('VHD'), key: 'vhd'},
          {label: gettext('VMDK'), key: 'vmdk'}
        ]
      })
      .append({
        label: gettext('Min. Size (bytes)'),
        name: 'size_min',
        isServer: true,
        singleton: true
      })
      .append({
        label: gettext('Max. Size (bytes)'),
        name: 'size_max',
        isServer: true,
        singleton: true
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
      ploop: gettext('PLOOP - Virtuozzo/Parallels Loopback Disk'),
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
   * @name imageProperties
   * @description resource properties for image module
   */
  function imageProperties(imagesService, statuses) {
    return {
      id: gettext('ID'),
      checksum: gettext('Checksum'),
      members: gettext('Members'),
      min_disk: gettext('Min. Disk'),
      min_ram: gettext('Min. RAM'),
      name: gettext('Name'),
      owner: gettext('Owner'),
      tags: gettext('Tags'),
      'updated_at': {label: gettext('Updated At'), filters: ['simpleDate'] },
      virtual_size: gettext('Virtual Size'),
      visibility: gettext('Visibility'),
      description: gettext('Description'),
      architecture: gettext('Architecture'),
      kernel_id: gettext('Kernel ID'),
      ramdisk_id: gettext('Ramdisk ID'),
      'created_at': {label: gettext('Created At'), filters: ['simpleDate'] },
      container_format: { label: gettext('Container Format'), filters: ['uppercase'] },
      disk_format: { label: gettext('Disk Format'), filters: ['noValue', 'uppercase'] },
      is_public: { label: gettext('Is Public'), filters: ['yesno'] },
      type: { label: gettext('Type')},
      'protected': { label: gettext('Protected'), filters: ['yesno'] },
      size: { label: gettext('Size'), filters: ['bytes'] },
      status: { label: gettext('Status'), values: statuses }
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
      IMAGE_UPLOAD_PROGRESS: 'horizon.app.core.images.IMAGE_UPLOAD_PROGRESS'
    };
  }

  config.$inject = [
    '$provide',
    '$windowProvider',
    '$routeProvider',
    'horizon.app.core.detailRoute'
  ];

  /**
   * @name config
   * @param {Object} $provide
   * @param {Object} $windowProvider
   * @param {Object} $routeProvider
   * @description Routes used by this module.
   * @returns {undefined} Returns nothing
   */
  function config($provide, $windowProvider, $routeProvider, detailRoute) {
    var path = $windowProvider.$get().STATIC_URL + 'app/core/images/';
    $provide.constant('horizon.app.core.images.basePath', path);

    $routeProvider.when('/project/images/:id', {
      redirectTo: goToAngularDetails
    });

    $routeProvider.when('/admin/images/:id/detail', {
      redirectTo: goToAngularDetails
    });

    $routeProvider.when('/project/images', {
      templateUrl: path + 'panel.html'
    });

    $routeProvider.when('/admin/images', {
      templateUrl: path + 'admin-panel.html'
    });

    function goToAngularDetails(params) {
      return detailRoute + 'OS::Glance::Image/' + params.id;
    }
  }

})();
