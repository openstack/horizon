/**
 * (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
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
    .module('horizon.framework.widgets.table')
    .directive('hzResourceTable', directive);

  directive.$inject = ['horizon.framework.widgets.basePath'];

  /**
   * @ngdoc directive
   * @scope
   * @name hzResourceTable
   * @description
   * This directive produces a table and accompanying components that describe
   * a list of resources of the given type.  Based on information in the
   * registry, the batch, global, and item-level actions are presented as
   * appropriate.  Search capabilities are also provided.  The table contents
   * are responsive to actions' promise resolutions, updating contents when
   * they are likely to have changed.  This directive allows for the rapid
   * development of standard resource tables without having to rewrite
   * boilerplate controllers, markup, etc.
   *
   * @property resource-type-name {string}
   * The resource name in the registry
   *
   * @property track-by {string} (optional)
   * The track-by string to pass to the hz-generic-table
   *
   * @property list-function-extra-params {object} (optional)
   * Extra parameters required by this resource type's list function.
   * For example, if the list function requires a parent container ID.
   *
   * @example
   ```
   <div>Here's some content above the table.</div>
     <hz-resource-table
        resource-type-name="OS::Cinder::Volume"
        track-by="updated_at"
        list-function-extra-params="{region: 1234}">
     </hz-resource-table>
   <div>Here's some content below the table.</div>
   ```
   */

  function directive(basePath) {

    var directive = {
      restrict: 'E',
      scope: {
        resourceTypeName: '@',
        trackBy: '@?',
        listFunctionExtraParams: '=?'
      },
      bindToController: true,
      templateUrl: basePath + 'table/hz-resource-table.html',
      controller: "horizon.framework.widgets.table.ResourceTableController as ctrl"
    };

    return directive;
  }
})();
