/*
 * Copyright 2015 IBM Corp.
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

  describe('transfer-table controller', function() {

    beforeEach(module('templates'));
    beforeEach(module('smart-table'));
    beforeEach(module('horizon.framework'));

    var log, params, scope;
    beforeEach(module(function($provide) {
      // we will mock scope and timeout in this test
      // because we aren't concern with rendering results
      var timeout = function(fn) { fn(); };

      // we will mock parse and attrs
      // because we want to control the parameters
      log = { error: function() {} };
      var attrs = angular.noop;
      var parse = function(attr) {
        return function() {
          return attr ? attr : {};
        };
      };

      $provide.value('$timeout', timeout);
      $provide.value('$parse', parse);
      $provide.value('$attrs', attrs);
      $provide.value('$log', log);
    }));

    beforeEach(inject(function($injector, _$rootScope_) {
      scope = _$rootScope_.$new();
      params = {
        '$scope': scope,
        '$timeout': $injector.get('$timeout'),
        '$parse': $injector.get('$parse'),
        '$attrs': $injector.get('$attrs'),
        '$log': $injector.get('$log'),
        'helpText': {},
        'limits': { maxAllocation: 1 }
      };
    }));

    function generateItems(count) {
      var itemList = [];
      for (var index = 0; index < count; index++) {
        itemList[index] = { id: index };
      }
      return itemList;
    }

    //////////

    describe('initialization code', function() {

      var controllerProvider;
      beforeEach(inject(function($controller) {
        controllerProvider = $controller;
        spyOn(log, 'error');
      }));

      it('should log error on init with bad model', testBadModel);
      it('should initialize IDs with good model', testGoodModel);

      function testBadModel() {
        params.$attrs = { trModel: { available: 'abc', allocated: 123 } };
        controllerProvider('transferTableController', params);
        expect(log.error).toHaveBeenCalled();
        expect(log.error.calls.count()).toEqual(2);
      }

      function testGoodModel() {
        var availableCount = 10;
        var allocatedCount = 5;
        params.$attrs = {
          trModel: {
            available: generateItems(availableCount),
            allocated: generateItems(allocatedCount)
          }
        };
        var trCtrl = controllerProvider('transferTableController', params);
        expect(log.error).not.toHaveBeenCalled();
        expect(Object.keys(trCtrl.allocatedIds).length).toEqual(allocatedCount);
        expect(trCtrl.allocated.sourceItems.length).toEqual(allocatedCount);
        expect(trCtrl.available.sourceItems.length).toEqual(availableCount);
      }

    });

    describe('core functions', function() {

      var trCtrl;
      beforeEach(inject(function($controller) {
        trCtrl = $controller('transferTableController', params);
      }));

      it('should always allocate if allocation limit is negative', testLimitNegative);
      it('should not allocate if allocation limit is reached', testLimitMaxed);
      it('should swap out allocated item if allocation limit is one', testLimitOne);
      it('should deallocate by moving item from allocated to available list', testDeallocate);
      it('should update allocated on reorder', testUpdateAllocated);
      it('should update allocatedIds if allocated change', testAllocatedIds);
      it('should toggle the views correctly on request', testToggleView);

      //////////

      function testToggleView() {
        trCtrl.toggleView('allocated');
        trCtrl.toggleView('available');
        expect(trCtrl.views.allocated).toEqual(false);
        expect(trCtrl.views.available).toEqual(false);
        trCtrl.toggleView('allocated');
        trCtrl.toggleView('available');
        expect(trCtrl.views.allocated).toEqual(true);
        expect(trCtrl.views.available).toEqual(true);
      }

      function testLimitNegative() {
        var itemCount = 10;
        trCtrl.limits.maxAllocation = -1;
        trCtrl.available.sourceItems = generateItems(itemCount);
        for (var index = 0; index < itemCount; index++) {
          trCtrl.allocate(trCtrl.available.sourceItems[index]);
        }
        expect(Object.keys(trCtrl.allocatedIds).length).toEqual(itemCount);
        expect(trCtrl.allocated.sourceItems.length).toEqual(itemCount);
        expect(trCtrl.numAllocated()).toEqual(itemCount);
        expect(trCtrl.numAvailable()).toEqual(0);
      }

      function testLimitMaxed() {
        var itemCount = 10;
        trCtrl.limits.maxAllocation = 5;
        trCtrl.available.sourceItems = generateItems(itemCount);
        for (var index = 0; index < itemCount; index++) {
          trCtrl.allocate(trCtrl.available.sourceItems[index]);
        }
        expect(Object.keys(trCtrl.allocatedIds).length).toEqual(trCtrl.limits.maxAllocation);
        expect(trCtrl.allocated.sourceItems.length).toEqual(trCtrl.limits.maxAllocation);
        expect(trCtrl.numAllocated()).toEqual(trCtrl.limits.maxAllocation);
        expect(trCtrl.numAvailable()).toEqual(itemCount - trCtrl.limits.maxAllocation);
      }

      function testLimitOne() {
        var itemCount = 10;
        trCtrl.limits.maxAllocation = 1;
        trCtrl.available.sourceItems = generateItems(itemCount);
        for (var index = 0; index < itemCount; index++) {
          trCtrl.allocate(trCtrl.available.sourceItems[index]);
        }
        expect(Object.keys(trCtrl.allocatedIds).length).toEqual(trCtrl.limits.maxAllocation);
        expect(trCtrl.allocated.sourceItems.length).toEqual(trCtrl.limits.maxAllocation);
        expect(trCtrl.numAllocated()).toEqual(trCtrl.limits.maxAllocation);
        expect(trCtrl.numAvailable()).toEqual(itemCount - trCtrl.limits.maxAllocation);
        // when limit is one, we swap out items
        // the ID of the last item allocated should be present
        expect('9' in trCtrl.allocatedIds).toEqual(true);
      }

      function testDeallocate() {
        trCtrl.available.sourceItems = generateItems(1);
        var item = trCtrl.available.sourceItems[0];
        trCtrl.allocate(item);
        trCtrl.deallocate(item);
        expect(item.id in trCtrl.allocatedIds).toEqual(false);
        expect(trCtrl.allocated.sourceItems.indexOf(item)).toEqual(-1);
        expect(trCtrl.numAllocated()).toEqual(0);
        expect(trCtrl.numAvailable()).toEqual(1);
      }

      function testAllocatedIds() {
        expect(trCtrl.allocatedIds).toEqual({});

        trCtrl.allocated.sourceItems = [{id: 1}, {id: 2}];
        scope.$apply();

        expect(trCtrl.allocatedIds).toEqual({1: true, 2: true});
      }

      function testUpdateAllocated() {
        var orderedItems = [1,2,3,4];
        trCtrl.updateAllocated(null, null, orderedItems);
        expect(trCtrl.allocated.sourceItems).toEqual(orderedItems);
        expect(trCtrl.numAllocated()).toEqual(orderedItems.length);
      }

    }); // end of core functions
  }); // end of transfer-table controller
})(); // end of IIFE
