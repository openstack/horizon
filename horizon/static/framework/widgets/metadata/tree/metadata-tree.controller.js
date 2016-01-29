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
    .controller('MetadataTreeController', MetadataTreeController);

  MetadataTreeController.$inject = [
    'horizon.framework.widgets.metadata.tree.service',
    'horizon.framework.widgets.metadata.tree.defaults'
  ];

  /**
   * @ngdoc controller
   * @name MetadataTreeController
   * @description
   * Controller used by `metadataTree`
   */
  function MetadataTreeController(metadataTreeService, defaults) {
    var ctrl = this;

    ctrl.availableFilter = availableFilter;
    ctrl.quickFilter = quickFilter;
    ctrl.text = angular.extend({}, defaults.text, ctrl.text);
    if (!ctrl.tree) {
      ctrl.tree = new metadataTreeService.Tree(ctrl.available, ctrl.existing);
    }
    ctrl.customItem = '';
    ctrl.filterText = {
      available: '',
      existing: ''
    };

    function availableFilter(item) {
      return !item.added && item.visible;
    }

    /**
     * @ngdoc method
     * @name MetadataTreeController.quickFilter
     * @description
     * Method used for filtering the list of available metadata items based on a user entered
     * string value. The list of items is filtered such that any leaf with a display value or
     * property name matching the provided string will be displayed. Parent items of any matching
     * leaf are also displayed so context and the tree structure are preserved.
     * @param {object} item The metadata tree item to filter.
     * @return {boolean} true if item matches, false otherwise
     */
    function quickFilter(item) {
      var text = ctrl.filterText.available;
      if (!text) {
        return true;
      }
      if (item.children.length > 0) {
        return item.children.filter(quickFilter).length > 0;
      }
      return item.label.indexOf(text) > -1 || item.leaf.name.indexOf(text) > -1;
    }
  }

})();
