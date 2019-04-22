/*
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

(function() {
  'use strict';

  describe('hz-generic-table controller', function() {
    var ctrl, listFunctionDeferred, actionResultDeferred,
      needsFilterFirstFunctionDeferred, $scope, settingCall;

    beforeEach(module('horizon.framework.util'));
    beforeEach(module('horizon.framework.conf'));
    beforeEach(module('horizon.framework.widgets.magic-search'));
    beforeEach(module('horizon.framework.widgets.table'));

    var resourceType = {
      type: 'OS::Test::Example',
      initActions: angular.noop,
      getTableColumns: angular.noop,
      list: angular.noop,
      globalActions: [],
      batchActions: [],
      itemInTransitionFunction: angular.noop,
      needsFilterFirstFunction: angular.noop,
      filterFacets: [
        {
          label: "Name",
          name: "name",
          singleton: true,
          isServer: true
        },
        {
          label: "Age",
          name: "age",
          singleton: true
        }
      ]
    };

    beforeEach(inject(function($rootScope, $controller, $q) {
      $scope = $rootScope.$new();
      var registry = {
        getTypeNameBySlug: angular.noop,
        getResourceType: angular.noop
      };

      listFunctionDeferred = $q.defer();
      actionResultDeferred = $q.defer();
      needsFilterFirstFunctionDeferred = $q.defer();
      spyOn(resourceType, 'needsFilterFirstFunction')
        .and
        .returnValue(needsFilterFirstFunctionDeferred.promise);
      spyOn(resourceType, 'list').and.returnValue(listFunctionDeferred.promise);
      spyOn(registry, 'getResourceType').and.returnValue(resourceType);

      var settings = {
        getSetting: function() {
          settingCall = $q.defer();
          return settingCall.promise;
        }
      };
      ctrl = $controller('horizon.framework.widgets.table.ResourceTableController', {
        $scope: $scope,
        'horizon.framework.conf.resource-type-registry.service': registry,
        'horizon.app.core.openstack-service-api.settings': settings},
        {resourceTypeName: 'OS::Test::Example'});
      $scope.ctrl = ctrl;
      $scope.$apply();
    }));

    it('exists', function() {
      expect(ctrl).toBeDefined();
    });

    it('sets itemsSrc to the response data', function() {
      needsFilterFirstFunctionDeferred.resolve(false);
      listFunctionDeferred.resolve({data: {items: [1,2,3]}});
      $scope.$apply();
      expect(ctrl.itemsSrc).toEqual([1,2,3]);
    });

    it('should not set itemsSrc to the response data if needsFilterFirst is true', function() {
      needsFilterFirstFunctionDeferred.resolve(true);
      $scope.$apply();
      expect(ctrl.itemsSrc).toEqual([]);
    });

    describe('server search handler', function() {

      var events;
      beforeEach(inject(function($injector) {
        events = $injector.get('horizon.framework.widgets.magic-search.events');
      }));

      it('passes search parameters to the list function', function() {
        var input = {
          magicSearchQuery: "name=happy&age=100&height=72"
        };
        needsFilterFirstFunctionDeferred.resolve(false);
        resourceType.list.calls.reset();
        $scope.$broadcast(events.SERVER_SEARCH_UPDATED, input);
        $scope.$apply();
        expect(resourceType.list)
          .toHaveBeenCalledWith({name: 'happy', age: '100', height: '72'});
      });

      it('should not list if needsFilterFirst is set to true ' +
         'and no search parameters were provided', function() {
        var input = {
          magicSearchQuery: ""
        };
        needsFilterFirstFunctionDeferred.resolve(true);
        resourceType.list.calls.reset();
        $scope.$broadcast(events.SERVER_SEARCH_UPDATED, input);
        $scope.$apply();
        expect(resourceType.list.calls.count()).toBe(0);
      });

      it('should list when needsFilterFirst is set to true' +
         ' and server-side search parameters were provided', function() {
        var input = {
          magicSearchQuery: "name=happy&age=100"
        };
        needsFilterFirstFunctionDeferred.resolve(true);
        resourceType.list.calls.reset();
        $scope.$broadcast(events.SERVER_SEARCH_UPDATED, input);
        $scope.$apply();
        expect(resourceType.list)
          .toHaveBeenCalledWith({name: 'happy', age: '100'});
      });
    });

    describe('data watchers', function() {

      var events;
      beforeEach(inject(function($injector) {
        events = $injector.get('horizon.framework.widgets.magic-search.events');
      }));

      it('lists resources on resourceTypeName change', function() {
        delete ctrl.resourceType;
        ctrl.resourceTypeName = 'Test::FooBar';
        $scope.$apply();
        expect(ctrl.resourceType).toEqual(resourceType);
      });

      it('does not list resources on resourceTypeName undefined', function() {
        ctrl.resourceTypeName = 'Test::FooBar';
        $scope.$apply();
        ctrl.resourceType.list.calls.reset();
        ctrl.resourceTypeName = undefined;
        $scope.$apply();
        expect(resourceType.list.calls.count()).toBe(0);
      });

      it('lists resources on listFunctionExtraParams change', function() {
        needsFilterFirstFunctionDeferred.resolve(false);
        ctrl.listFunctionExtraParams = {data: 'foobar'};
        resourceType.list.calls.reset();
        $scope.$apply();
        expect(resourceType.list).toHaveBeenCalled();
      });

      it('does not list resources on listFunctionExtraParams undefined', function() {
        ctrl.listFunctionExtraParams = {data: 'foobar'};
        $scope.$apply();
        ctrl.listFunctionExtraParams = undefined;
        resourceType.list.calls.reset();
        $scope.$apply();
        expect(resourceType.list.calls.count()).toBe(0);
      });

      it('does not list resources on listFunctionExtraParams change ' +
        'if resourceType undefined', function() {
        delete ctrl.resourceType;
        ctrl.listFunctionExtraParams = {data: 'foobar'};
        resourceType.list.calls.reset();
        $scope.$apply();
        expect(resourceType.list.calls.count()).toBe(0);
      });

      it('passes listFunctionExtraParams to list function', function() {
        needsFilterFirstFunctionDeferred.resolve(false);
        ctrl.listFunctionExtraParams = {data: 'foobar'};
        resourceType.list.calls.reset();
        $scope.$apply();
        expect(resourceType.list).toHaveBeenCalledWith({data: 'foobar'});
      });

      it('merges listfunctionExtraParams with new search query', function() {
        ctrl.listFunctionExtraParams = {data: 'foobar'};
        var input = {
          magicSearchQuery: "name=happy&age=100&height=72"
        };
        needsFilterFirstFunctionDeferred.resolve(false);
        resourceType.list.calls.reset();
        $scope.$broadcast(events.SERVER_SEARCH_UPDATED, input);
        $scope.$apply();
        expect(resourceType.list)
          .toHaveBeenCalledWith({name: 'happy', age: '100', height: '72', data: 'foobar'});
      });

      it('merges listFunctionExtraParams with prior search query', function() {
        var input = {
          magicSearchQuery: "name=happy&age=100&height=72"
        };
        $scope.$broadcast(events.SERVER_SEARCH_UPDATED, input);
        needsFilterFirstFunctionDeferred.resolve(false);
        resourceType.list.calls.reset();
        ctrl.listFunctionExtraParams = {data: 'foobar'};
        $scope.$apply();
        expect(resourceType.list)
          .toHaveBeenCalledWith({name: 'happy', age: '100', height: '72', data: 'foobar'});
      });
    });

    describe('actionResultHandler', function() {
      beforeEach(function() {
        ctrl.itemsSrc = [{type: 'Something', id: -1}, {type: 'OS::Test::Example', id: 1}];
      });

      it('handles deleted items', function() {
        actionResultDeferred.resolve({deleted: [{type: 'ignored', id: 0},
          {type: 'OS::Test::Example', id: 1}]});
        ctrl.actionResultHandler(actionResultDeferred.promise);
        $scope.$apply();
        expect(ctrl.itemsSrc).toEqual([{type: 'Something', id: -1}]);
      });

      it('handles updated items', function() {
        needsFilterFirstFunctionDeferred.resolve(false);
        actionResultDeferred.resolve({updated: [{type: 'OS::Test::Example', id: 1}]});
        ctrl.actionResultHandler(actionResultDeferred.promise);
        resourceType.list.calls.reset();
        $scope.$apply();
        expect(resourceType.list).toHaveBeenCalled();
      });

      it('handles created items', function() {
        needsFilterFirstFunctionDeferred.resolve(false);
        actionResultDeferred.resolve({created: [{type: 'OS::Test::Example', id: 1}]});
        ctrl.actionResultHandler(actionResultDeferred.promise);
        resourceType.list.calls.reset();
        $scope.$apply();
        expect(resourceType.list).toHaveBeenCalled();
      });

      it('handles failed items', function() {
        actionResultDeferred.resolve({failed: [{type: 'OS::Test::Example', id: 1}]});
        ctrl.actionResultHandler(actionResultDeferred.promise);
        resourceType.list.calls.reset();
        $scope.$apply();
        expect(resourceType.list).not.toHaveBeenCalled();
      });

      it('handles falsy results', function() {
        needsFilterFirstFunctionDeferred.resolve(false);
        actionResultDeferred.resolve(false);
        ctrl.actionResultHandler(actionResultDeferred.promise);
        resourceType.list.calls.reset();
        $scope.$apply();
        expect(resourceType.list).toHaveBeenCalled();
      });
    });

    describe('item in transition function', function() {
      it('it calls resource type itemInTransitionFunction', function() {
        spyOn(resourceType, "itemInTransitionFunction");
        ctrl.itemInTransitionFunction();
        expect(resourceType.itemInTransitionFunction.calls.count()).toBe(1);
      });
    });

  });

})();
