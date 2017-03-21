/*
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

(function() {
  'use strict';

  describe('hz-resource-property directive', function() {
    var $compile, $rootScope, $scope, registry, tableColumnInfo;
    var testResource = {
      getProperties: function() {
        return {name: {label: 'display name'}};
      },
      getTableColumns: function() {
        return tableColumnInfo;
      }
    };

    beforeEach(module('templates'));
    beforeEach(module('horizon.framework'));

    beforeEach(inject(function(_$compile_, _$rootScope_, $injector) {
      registry = $injector.get('horizon.framework.conf.resource-type-registry.service');
      $compile = _$compile_;
      $rootScope = _$rootScope_;
      $scope = $rootScope.$new();
    }));

    it("sets class when item's priority is set 1", function() {
      $scope.item = {name: 'value of name'};
      tableColumnInfo = [{id: 'name', priority: 1 }];
      spyOn(registry, 'getResourceType').and.returnValue(testResource);
      var element = $compile(
       "<hz-resource-property" +
       " resource-type-name='resourceTypeName' item='item' prop-name='name'>" +
       "</hz-resource-property>")($scope);
      $scope.$digest();
      expect(element.hasClass("rsp-p1")).toBeTruthy();
    });

    it("sets class when item's priority is set 2", function() {
      $scope.item = {name: 'value of name'};
      tableColumnInfo = [{id: 'name', priority: 2 }];
      spyOn(registry, 'getResourceType').and.returnValue(testResource);
      var element = $compile(
        "<hz-resource-property" +
        " resource-type-name='resourceTypeName' item='item' prop-name='name'>" +
        "</hz-resource-property>")($scope);
      $scope.$digest();
      expect(element.hasClass("rsp-alt-p2")).toBeTruthy();
    });

    it("sets class when item's priority is set illegally", function() {
      $scope.item = {name: 'value of name'};
      tableColumnInfo = [{id: 'name', priority: 0 }];
      spyOn(registry, 'getResourceType').and.returnValue(testResource);
      var element = $compile(
        "<hz-resource-property" +
        " resource-type-name='resourceTypeName' item='item' prop-name='name'>" +
        "</hz-resource-property>")($scope);
      $scope.$digest();
      expect(element.hasClass("rsp-p1")).toBeTruthy();
    });

    it("sets class when item's priority is not set", function() {
      $scope.item = {name: 'value of name'};
      // table column doesn't have an attribute of 'priority'
      tableColumnInfo = [{id: 'name'}];
      spyOn(registry, 'getResourceType').and.returnValue(testResource);
      var element = $compile(
        "<hz-resource-property" +
        " resource-type-name='resourceTypeName' item='item' prop-name='name'>" +
        "</hz-resource-property>")($scope);
      $scope.$digest();
      expect(element.hasClass("rsp-p1")).toBeTruthy();
    });
  });

})();
