/*
 * Copyright 2015 IBM Corp.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function() {
  'use strict';

  angular
    .module('horizon.framework.widgets.table')
    .directive('hzNoItems', hzNoItems);

  hzNoItems.$inject = ['horizon.framework.widgets.basePath'];

  /**
   * @ngdoc directive
   * @name horizon.framework.widgets.table.directive:hzNoItems
   * @description
   * The `hzNoItems` directive provides a default message when there are no items
   * in the table. Implementations can provide a custom message by specifying
   * an optional message attribute.
   * @restrict A
   *
   * @example
   * ```
   * <tr hz-no-items
   *   items="table.iusers"
   *   message="table.noUsersText">
   * </tr>
   *
   * or
   *
   * <tr hz-no-items
   *   items="table.iusers">
   * </tr>
   * ```
   */
  function hzNoItems(basePath) {

    var directive = {
      restrict: 'A',
      require: '^hzTable',
      templateUrl: basePath + 'table/hz-no-items.html',
      scope: {
        items: '=',
        message: '=?'
      }
    };
    return directive;
  }
}());
