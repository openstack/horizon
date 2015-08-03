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
    .directive('metadataTreeUnique', metadataTreeUnique);

  /**
   * @ngdoc directive
   * @name metadataTreeUnique
   * @restrict A
   *
   * @description
   * The `metadataTreeUnique` helper directive provides validation
   * for field which value should be unique new Item
   */
  function metadataTreeUnique() {
    var directive = {
      restrict: 'A',
      require: ['^metadataTree', 'ngModel'],
      link: link
    };

    return directive;

    function link(scope, elm, attrs, controllers) {
      var metadataTree = controllers[0];
      var ngModel = controllers[1];
      ngModel.$validators.unique = function (modelValue, viewValue) {
        return !metadataTree.tree.flatTree.some(function (item) {
          return item.leaf && item.leaf.name === viewValue;
        });
      };
    }
  }

})();
