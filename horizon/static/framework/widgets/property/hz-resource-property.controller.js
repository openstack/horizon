/*
 * (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
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
    .module('horizon.framework.widgets.property')
    .controller('horizon.framework.widgets.property.hzResourcePropertyController', controller);

  controller.$inject = [
    'horizon.framework.conf.resource-type-registry.service'
  ];

  function controller(registry) {
    var ctrl = this;

    // 'Public' Controller members

    // 'config' is the configuration for how to output the field, and 'config.id'
    // is the property name itself.
    ctrl.config = registry.getResourceType(ctrl.resourceTypeName).getProperties()[ctrl.propName];
    ctrl.config.id = ctrl.propName;

    angular.forEach(registry.getResourceType(ctrl.resourceTypeName).getTableColumns(),
      function(column) {
        if (column.id === ctrl.propName) {
          ctrl.config.priority = column.priority;
        }
      }
    );
  }

})();
