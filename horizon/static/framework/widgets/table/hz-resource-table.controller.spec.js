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
    var ctrl, listFunctionDeferred, $timeout, actionResultDeferred;

    beforeEach(module('horizon.framework.util'));
    beforeEach(module('horizon.framework.conf'));
    beforeEach(module('horizon.framework.widgets.table'));

    var resourceType = {
      type: 'OS::Test::Example',
      getTableColumns: angular.noop,
      listFunction: angular.noop,
      globalActions: [],
      batchActions: []
    };

    beforeEach(inject(function($controller, $q, _$timeout_) {
      $timeout = _$timeout_;
      var registry = {
        getTypeNameBySlug: angular.noop,
        getResourceType: angular.noop,
        initActions: angular.noop
      };

      listFunctionDeferred = $q.defer();
      actionResultDeferred = $q.defer();
      spyOn(resourceType, 'listFunction').and.returnValue(listFunctionDeferred.promise);
      spyOn(registry, 'getResourceType').and.returnValue(resourceType);

      ctrl = $controller('horizon.framework.widgets.table.ResourceTableController', {
        $scope: {},
        'horizon.framework.conf.resource-type-registry.service': registry},
        {resourceTypeName: 'OS::Test::Example'});
    }));

    it('exists', function() {
      expect(ctrl).toBeDefined();
    });

    it('sets itemsSrc to the response data', function() {
      listFunctionDeferred.resolve({data: {items: [1,2,3]}});
      $timeout.flush();
      expect(ctrl.itemsSrc).toEqual([1,2,3]);
    });

    describe('actionResultHandler', function() {
      beforeEach(function() {
        ctrl.itemsSrc = [{type: 'Something', id: -1}, {type: 'OS::Test::Example', id: 1}];
      });

      it('handles deleted items', function() {
        actionResultDeferred.resolve({deleted: [{type: 'ignored', id: 0},
          {type: 'OS::Test::Example', id: 1}]});
        var promise = ctrl.actionResultHandler(actionResultDeferred.promise);
        promise.then(function() {
          expect(ctrl.itemsSrc).toEqual([{type: 'Something', id: -1}]);
        });
        $timeout.flush();
      });

      it('handles updated items', function() {
        actionResultDeferred.resolve({updated: [{type: 'OS::Test::Example', id: 1}]});
        var promise = ctrl.actionResultHandler(actionResultDeferred.promise);
        resourceType.listFunction.calls.reset();
        promise.then(function() {
          expect(resourceType.listFunction).toHaveBeenCalled();
        });
        $timeout.flush();
      });

      it('handles created items', function() {
        actionResultDeferred.resolve({created: [{type: 'OS::Test::Example', id: 1}]});
        var promise = ctrl.actionResultHandler(actionResultDeferred.promise);
        resourceType.listFunction.calls.reset();
        promise.then(function() {
          expect(resourceType.listFunction).toHaveBeenCalled();
        });
        $timeout.flush();
      });

      it('handles failed items', function() {
        actionResultDeferred.resolve({failed: [{type: 'OS::Test::Example', id: 1}]});
        var promise = ctrl.actionResultHandler(actionResultDeferred.promise);
        resourceType.listFunction.calls.reset();
        promise.then(function() {
          expect(resourceType.listFunction).not.toHaveBeenCalled();
        });
        $timeout.flush();
      });

      it('handles falsy results', function() {
        actionResultDeferred.resolve(false);
        var promise = ctrl.actionResultHandler(actionResultDeferred.promise);
        resourceType.listFunction.calls.reset();
        promise.then(function() {
          expect(resourceType.listFunction).toHaveBeenCalled();
        });
        $timeout.flush();
      });
    });

  });

})();
