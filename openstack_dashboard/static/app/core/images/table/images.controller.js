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

  angular
    .module('horizon.app.core.images')
    .controller('horizon.app.core.images.table.ImagesController', ImagesTableController);

  ImagesTableController.$inject = [
    '$q',
    '$scope',
    'horizon.app.core.images.detailsRoute',
    'horizon.app.core.images.events',
    'horizon.app.core.images.resourceType',
    'horizon.app.core.openstack-service-api.glance',
    'horizon.app.core.openstack-service-api.userSession',
    'horizon.framework.conf.resource-type-registry.service',
    'imageVisibilityFilter'
  ];

  /**
   * @ngdoc controller
   * @name horizon.app.core.images.table.ImagesTableController
   *
   * @description
   * Controller for the images table.
   * Serves as the focal point for table actions.
   */
  function ImagesTableController(
    $q,
    $scope,
    detailsRoute,
    events,
    imageResourceType,
    glance,
    userSession,
    typeRegistry,
    imageVisibilityFilter
  ) {
    var ctrl = this;

    ctrl.detailsRoute = detailsRoute;

    ctrl.checked = {};

    ctrl.images = [];
    ctrl.imagesSrc = [];
    ctrl.metadataDefs = null;

    ctrl.getItemActions = typeRegistry.getItemActionsFunction(imageResourceType);
    ctrl.getBatchActions = typeRegistry.getBatchActionsFunction(imageResourceType);

    var deleteWatcher = $scope.$on(events.DELETE_SUCCESS, onDeleteSuccess);

    $scope.$on('$destroy', destroy);

    init();

    ////////////////////////////////

    function init() {
      typeRegistry.initActions(imageResourceType, $scope);
      $q.all(
        {
          images: glance.getImages(),
          session: userSession.get()
        }
      ).then(onInitialized);
    }

    function onInitialized(d) {
      ctrl.imagesSrc.length = 0;
      angular.forEach(d.images.data.items, function itemFilter (image) {
        //This sets up data expected by the table for display or sorting.
        image.filtered_visibility = imageVisibilityFilter(image, d.session.project_id);
        ctrl.imagesSrc.push(image);
      });

      // MetadataDefinitions are only used in expandable rows and are non-critical.
      // Defer loading them until critical data is loaded.
      applyMetadataDefinitions();
    }

    function onDeleteSuccess(e, removedImageIds) {
      ctrl.imagesSrc = difference(ctrl.imagesSrc, removedImageIds, 'id');
      e.stopPropagation();

      // after deleting the items
      // we need to clear selected items from table controller
      $scope.$emit('hzTable:clearSelected');
    }

    function difference(currentList, otherList, key) {
      return currentList.filter(filter);

      function filter(elem) {
        return otherList.filter(function filterDeletedItem(deletedItem) {
          return deletedItem === elem[key];
        }).length === 0;
      }
    }

    function destroy() {
      deleteWatcher();
    }

    function applyMetadataDefinitions() {
      glance.getNamespaces({resource_type: imageResourceType}, true)
        .then(function setMetadefs(data) {
          ctrl.metadataDefs = data.data.items;
        });
    }

  }

})();
