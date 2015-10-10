/*
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function () {
  'use strict';

  angular
    .module('horizon.app.core.images')
    .controller('horizon.app.core.images.steps.UpdateMetadataController', UpdateMetadataController);

  UpdateMetadataController.$inject = [
    '$scope',
    '$q',
    'horizon.app.core.images.events',
    'horizon.app.core.metadata.service',
    'horizon.framework.widgets.metadata.tree.service'
  ];

  /**
   * @ngdoc controller
   * @name MetadataController
   * @description
   * Controller used by Image for Update Metadata
   */
  function UpdateMetadataController(
    $scope,
    $q,
    events,
    metadataService,
    metadataTreeService
  ) {
    var ctrl = this;

    ctrl.tree = new metadataTreeService.Tree([], []);

    /* eslint-enable angular/ng_controller_as */
    $scope.$watchCollection(getTree, onMetadataChanged);
    /* eslint-enable angular/ng_controller_as */

    $scope.imagePromise.then(init);

    ////////////////////////////////

    function init(response) {
      var image = response.data;
      $q.all({
        available: metadataService.getNamespaces('image'),
        existing: metadataService.getMetadata('image', image.id)
      }).then(onMetadataGet);
    }

    function onMetadataGet(response) {
      ctrl.tree = new metadataTreeService.Tree(
        response.available.data.items,
        response.existing.data
      );
    }

    function getTree() {
      return ctrl.tree.getExisting();
    }

    function onMetadataChanged(newValue, oldValue) {
      if (newValue !== oldValue) {
        $scope.$emit(events.IMAGE_METADATA_CHANGED, newValue);
      }
    }

  }
})();
