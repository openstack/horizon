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
    'horizon.framework.util.actions.action-result.service',
    'imageVisibilityFilter'
  ];

  /**
   * @ngdoc controller
   * @name horizon.app.core.images.table.ImagesTableController
   *
   * @param {Object} $q
   * @param {Object} $scope
   * @param {String} detailsRoute
   * @param {Object} events
   * @param {Object} imageResourceType
   * @param {Object} glance
   * @param {Object} userSession
   * @param {Object} typeRegistry
   * @param {Object} imageVisibilityFilter
   * @description
   * Controller for the images table.
   * Serves as the focal point for table actions.
   *
   * @returns {undefined} No return value
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
    actionResultService,
    imageVisibilityFilter
  ) {
    var ctrl = this;

    ctrl.detailsRoute = detailsRoute;

    ctrl.checked = {};

    ctrl.metadataDefs = null;

    ctrl.imageResourceType = typeRegistry.getResourceType(imageResourceType);
    ctrl.actionResultHandler = actionResultHandler;

    typeRegistry.initActions(imageResourceType, $scope);
    loadImages();

    ////////////////////////////////

    function loadImages() {
      ctrl.images = [];
      ctrl.imagesSrc = [];
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

    function difference(currentList, otherList, key) {
      return currentList.filter(filter);

      function filter(elem) {
        return otherList.filter(function filterDeletedItem(deletedItem) {
          return deletedItem === elem[key];
        }).length === 0;
      }
    }

    function applyMetadataDefinitions() {
      glance.getNamespaces({resource_type: imageResourceType}, true)
        .then(function setMetadefs(data) {
          ctrl.metadataDefs = data.data.items;
        });
    }

    function actionResultHandler(returnValue) {
      return $q.when(returnValue, actionSuccessHandler);
    }

    function actionSuccessHandler(result) { // eslint-disable-line no-unused-vars

      // The action has completed (for whatever "complete" means to that
      // action. Notice the view doesn't really need to know the semantics of the
      // particular action because the actions return data in a standard form.
      // That return includes the id and type of each created, updated, deleted
      // and failed item.
      //
      // This handler is also careful to check the type of each item. This
      // is important because actions which create non-images are launched from
      // the images page (like create "volume" from image).
      var deletedIds, updatedIds, createdIds, failedIds;

      if ( result ) {
        // Reduce the results to just image ids ignoring other types the action
        // may have produced
        deletedIds = actionResultService.getIdsOfType(result.deleted, imageResourceType);
        updatedIds = actionResultService.getIdsOfType(result.updated, imageResourceType);
        createdIds = actionResultService.getIdsOfType(result.created, imageResourceType);
        failedIds = actionResultService.getIdsOfType(result.failed, imageResourceType);

        // Handle deleted images
        if (deletedIds.length) {
          ctrl.imagesSrc = difference(ctrl.imagesSrc, deletedIds,'id');
        }

        // Handle updated and created images
        if ( updatedIds.length || createdIds.length ) {
          // Ideally, get each created image individually, but
          // this is simple and robust for the common use case.
          // TODO: If we want more detailed updates, we could do so here.
          loadImages();
        }

        // Handle failed images
        if ( failedIds.length ) {
          // Do nothing for now
        }

      } else {
        // promise resolved, but no result returned. Because the action didn't
        // tell us what happened...reload the displayed images just in case.
        loadImages();
      }
    }

  }

})();
