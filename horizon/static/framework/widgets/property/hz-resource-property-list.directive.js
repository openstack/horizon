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
    .module('horizon.framework.widgets.property')
    .directive('hzResourcePropertyList', directive);

  directive.$inject = [
    'horizon.framework.widgets.basePath'
  ];

  /**
   * @ngdoc directive
   * @name hzResourcePropertyList
   * @description
   * This directive is intended to be used with the resource registry.  It currently
   * displays sets of properties registered for the given type, grouped into
   * label/values.
   *
   * The directive displays the groups proportionately based on the number of
   * property groups presented.  The proportions are based off a 12-column system
   * such as Bootstrap, and any number of columns between 1 and 12 may be used.
   *
   * There is no limit to the number of properties within a group.
   *
   * @example
   * The following would produce three sets of property lists, each entry with
   * a label and value, based on the 'item' object given, and using registrations
   * for the given type ('OS::Neutron::Net') to inform how to format each
   * property.  The 'cls' property will place the 'dl-horizontal' class on the <dl>
   * element.
   *
   * The following will produce three sets of lists.  The first group, for example,
   * will contain the label and value of the 'name' property and the label and value
   * of the 'id' property.
   ```
   <hz-resource-property-list
     resource-type-name="OS::Neutron::Net"
     item="item"
     cls="dl-horizontal"
     property-groups="[
       ['name', 'id'],
       ['shared', 'router__external'],
       ['status', 'admin_state_up']]">
   </hz-resource-property-list>
   ```
   *
   */
  function directive(basePath) {

    var directiveConf = {
      restrict: 'E',
      scope: {
        resourceTypeName: "@",
        propertyGroups: "=",
        cls: "@?",
        item: "="
      },
      link: link,
      templateUrl: basePath + 'property/hz-resource-property-list.html'
    };
    return directiveConf;

    function link(scope) {
      scope.getBootstrapColumnSpan = getBootstrapColumnSpan;

      function getBootstrapColumnSpan(columns) {
        return Math.floor(12 / columns.length);
      }
    }

  }
})();
