/*
 * Copyright 2015, Intel Corp.
 *
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
    .module('horizon.framework.widgets.metadata.tree')
    .directive('metadataTree', metadataTree);

  metadataTree.$inject = ['horizon.framework.widgets.metadata.tree.basePath'];

  /**
   * @ngdoc directive
   * @name metadataTree
   * @restrict E
   * @scope
   *
   * @description
   * The `metadataTree` directive provide support for modifying existing
   * metadata properties and adding new from metadata catalog.
   *
   * @param {Tree=} model Model binding
   * @param {object[]=} available List of available namespaces
   * @param {object=} existing Key-value pairs with existing properties
   * @param {object=} text Text override
   * @param {object=} form Existing items form binding
   */
  function metadataTree(path) {
    var directive = {
      bindToController: true,
      controller: 'MetadataTreeController as ctrl',
      restrict: 'E',
      scope: {
        tree: '=*?model',
        available: '=?',
        existing: '=?',
        text: '=?',
        metadataForm: '=?form'
      },
      templateUrl: path + 'metadata-tree.html'
    };

    return directive;
  }

})();
