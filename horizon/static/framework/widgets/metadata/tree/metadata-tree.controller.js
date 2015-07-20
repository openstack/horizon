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
      return !item.added && (
        ctrl.filterText.available.length === 0 ? item.visible : true);
    }
  }

})();
