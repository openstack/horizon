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
    .directive('metadataTreeItem', metadataTreeItem);

  metadataTreeItem.$inject = ['horizon.framework.widgets.metadata.tree.basePath'];

  /**
   * @ngdoc directive
   * @name metadataTreeItem
   * @restrict E
   * @scope
   *
   * @description
   * The `metadataTreeItem` helper directive displays proper field for
   * editing Item.leaf.value depending on Item.leaf.type
   *
   * @param {expression} action Action for button
   * @param {Item} item Item to display
   * @param {object} text Text override
   */
  function metadataTreeItem(path) {
    var directive = {
      bindToController: true,
      controller: 'MetadataTreeItemController as ctrl',
      restrict: 'E',
      scope: {
        action: '&',
        item: '=',
        text: '='
      },
      templateUrl: path + 'metadata-tree-item.html'
    };

    return directive;
  }

})();
