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
    .directive('hzResourceProperty', hzResourceProperty);

  hzResourceProperty.$inject = [
    '$log',
    'horizon.framework.widgets.basePath'
  ];

  /**
   * @ngdoc directive
   * @name hzResourceProperty
   * @description
   * This directive produces a label/value output of a property. It uses the
   * resource type registry to look up the resource type by name, then outputs
   * the named property on the given item, using the registry's knowledge of
   * how to output the property.
   * @example
   *
   *
   ```
   $scope.someObject = {somePropertyOnObject: 'myData'};

   <hz-resource-property resource-type-name="OS::Glance::Image"
                item="someObject"
                propName="somePropertyOnObject"></hz-resource-property>
   ```
   *
   */
  function hzResourceProperty($log, basePath) {

    var directiveConf = {
      restrict: 'E',
      scope: {
        resourceTypeName: "@",
        propName: "@",
        item: "="
      },
      bindToController: true,
      controller: 'horizon.framework.widgets.property.hzResourcePropertyController as ctrl',
      templateUrl: basePath + 'property/hz-resource-property.html',
      link: link
    };
    return directiveConf;

    ////

    function link(scope, element) {
      var config = scope.ctrl.config;
      var priority = config.priority ? config.priority : 1;
      if (!angular.isNumber(priority) || priority < 1) {
        priority = 1;
        $log.warn("Please set an integer of 1 or more for priority of hz-resource-property. " +
          "Otherwise priority is set 1, 1 is the highest priority and will not be hidden " +
          "from table row due to window narrowing.");
      }
      var style = priority > 1 ? 'rsp-alt-p' : 'rsp-p';
      element.addClass(style + priority);
    }
  }
})();
