/**
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
(function () {
  'use strict';

  describe('horizon.app.core.images.controller.CreateVolumeController', function () {

    var controller, quotaChartDefaults, $scope, $filter, getAbsoluteLimitsSpy, nova;

    var cinder = {
      getVolumeTypes: function() {
        return {
          success: function(callback) {
            return callback({items: [{name: 'volumeType'}, {name: 'lvmdriver-1'}]});
          }
        };
      },
      getDefaultVolumeType: function() {
        return {
          success: function(callback) {
            return callback({name: 'lvmdriver-1'});
          }
        };
      },
      getAvailabilityZones: function() {
        return {
          success: function(callback) {
            return callback({ items: [{zoneName: 'zone1'}] });
          }
        };
      },
      getAbsoluteLimits: angular.noop
    };

    beforeEach(module('horizon.app.core.images'));
    beforeEach(module('horizon.framework.widgets.charts'));
    beforeEach(module('horizon.framework.util.filters'));

    beforeEach(inject(function ($injector, _$rootScope_, _$filter_) {

      $scope = _$rootScope_.$new();
      $scope.image = {
        name: 'ImageName',
        size: 1024
      };

      $scope.stepModels = {};

      $scope.volumeForm = {
        $setValidity : angular.noop
      };

      controller = $injector.get('$controller');
      quotaChartDefaults = $injector.get('horizon.framework.widgets.charts.quotaChartDefaults');
      $filter = _$filter_;

      getAbsoluteLimitsSpy = spyOn(cinder, 'getAbsoluteLimits');
      getAbsoluteLimitsSpy.and.returnValue({
        success: function(callback) {
          return callback({
            maxTotalVolumeGigabytes: 20,
            totalVolumesUsed: 10,
            maxTotalVolumes: 50,
            totalGigabytesUsed: 10
          });
        }
      });

      spyOn($scope, '$watch').and.callThrough();
      spyOn($scope, '$emit').and.callThrough();
      spyOn($scope.volumeForm, '$setValidity');
    }));

    function createController() {
      return controller('horizon.app.core.images.steps.CreateVolumeController', {
        $scope: $scope,
        $filter: $filter,
        'horizon.app.core.openstack-service-api.cinder' : cinder,
        'horizon.app.core.openstack-service-api.nova' : nova,
        'horizon.framework.widgets.charts.quotaChartDefaults': quotaChartDefaults
      });
    }

    it('should initialize default values using cinder and nova apis', function() {
      getAbsoluteLimitsSpy.and.returnValue({
        success: function(callback) {
          return callback({
            maxTotalVolumeGigabytes: 2,
            totalVolumesUsed: 1,
            maxTotalVolumes: 5,
            totalGigabytesUsed: 1
          });
        }
      });

      var ctrl = createController();
      expect(ctrl.volumeTypes).toEqual([{name: 'volumeType'}, {name: 'lvmdriver-1'}]);
      expect(ctrl.availabilityZones).toEqual(['zone1']);
      expect(ctrl.image).toEqual({
        name: 'ImageName',
        size: 1024
      });
      expect(ctrl.sourceImage).toEqual('ImageName (1.00 KB)');
      expect(ctrl.volume.size).toEqual(1);
      expect(ctrl.volumeType).toEqual({name: 'lvmdriver-1'});
      expect(ctrl.maxTotalVolumeGigabytes).toEqual(2);
      expect(ctrl.maxTotalVolumes).toEqual(5);
      expect(ctrl.totalVolumesUsed).toEqual(1);
    });

    it('should setup the storage graph with default values', function() {
      getAbsoluteLimitsSpy.and.returnValue({
        success: function(callback) {
          return callback({
            maxTotalVolumeGigabytes: 2,
            totalVolumesUsed: 1,
            maxTotalVolumes: 5,
            totalGigabytesUsed: 1
          });
        }
      });

      var ctrl = createController();
      var graph = ctrl.storageQuota;

      expect(graph.title).toEqual('Volume and Snapshot Quota (GiB)');
      expect(graph.maxLimit).toEqual(2);
      expect(graph.label).toEqual('100%');

      var current = graph.data[0];
      expect(current.label).toEqual('Current Usage');
      expect(current.value).toEqual(1);
      expect(current.colorClass).toEqual('usage');

      var added = graph.data[1];
      expect(added.label).toEqual('Added');
      expect(added.value).toEqual(1);
      expect(added.colorClass).toEqual('added');

      var remaining = graph.data[2];
      expect(remaining.label).toEqual('Remaining');
      expect(remaining.value).toEqual(0);
      expect(remaining.colorClass).toEqual('remaining');
    });

    it('should setup the volume quota instance graph with default values', function() {
      getAbsoluteLimitsSpy.and.returnValue({
        success: function(callback) {
          return callback({
            maxTotalVolumeGigabytes: 2,
            totalVolumesUsed: 1,
            maxTotalVolumes: 5,
            totalGigabytesUsed: 1
          });
        }
      });

      var ctrl = createController();
      var graph = ctrl.volumeQuota;
      expect(graph.title).toEqual('Volume Quota');
      expect(graph.maxLimit).toEqual(5);
      expect(graph.data[0].value).toBe(1);
      expect(graph.data[1].value).toBe(1);
      // It's 40% because the two values above are added together
      // and taken over the maxTotal (2/5).
      expect(graph.label).toEqual('40%');

      var current = graph.data[0];
      expect(current).toEqual({label: 'Current Usage', value: 1, colorClass: 'usage'});

      var added = graph.data[1];
      expect(added).toEqual({label: 'Added', value: 1, colorClass: 'added'});

      var remaining = graph.data[2];
      expect(remaining).toEqual({label: 'Remaining', value: 3, colorClass: 'remaining'});
    });

    it('should update storage stats on volume size change', function() {
      getAbsoluteLimitsSpy.and.returnValue({
        success: function(callback) {
          return callback({
            maxTotalVolumeGigabytes: 2,
            totalVolumesUsed: 1,
            maxTotalVolumes: 5,
            totalGigabytesUsed: 1
          });
        }
      });

      var ctrl = createController();
      var graph = ctrl.storageQuota;
      var current = graph.data[0];
      var added = graph.data[1];
      var remaining = graph.data[2];

      ctrl.volume.size = 2;
      $scope.$apply();

      expect(current.value).toEqual(1);
      expect(added.value).toEqual(2);
      expect(remaining.value).toEqual(0);
      expect(graph.label).toEqual('150%');
      expect(graph.maxLimit).toEqual(2);
      expect(graph.overMax).toBeTruthy();
    });

    it('should not change if volume size is 0', function() {
      getAbsoluteLimitsSpy.and.returnValue({
        success: function(callback) {
          return callback({
            maxTotalVolumeGigabytes: 2,
            totalVolumesUsed: 1,
            maxTotalVolumes: 5,
            totalGigabytesUsed: 1
          });
        }
      });

      var ctrl = createController();
      var graph = ctrl.storageQuota;
      var current = graph.data[0];
      var added = graph.data[1];
      var remaining = graph.data[2];

      ctrl.volume.size = 0;
      $scope.$apply();

      expect(current.value).toEqual(1);
      expect(added.value).toEqual(0);
      expect(remaining.value).toEqual(1);
      expect(graph.label).toEqual('50%');
      expect(graph.maxLimit).toEqual(2);
    });

    it('should not change if volume size is < 0', function() {
      getAbsoluteLimitsSpy.and.returnValue({
        success: function(callback) {
          return callback({
            maxTotalVolumeGigabytes: 2,
            totalVolumesUsed: 1,
            maxTotalVolumes: 5,
            totalGigabytesUsed: 1
          });
        }
      });

      var ctrl = createController();
      var graph = ctrl.storageQuota;
      var current = graph.data[0];
      var added = graph.data[1];
      var remaining = graph.data[2];

      ctrl.volume.size = -1;
      $scope.$apply();

      expect(current.value).toEqual(current.value);
      expect(added.value).toEqual(added.value);
      expect(remaining.value).toEqual(remaining.value);
      expect(graph.label).toEqual(graph.label);
      expect(graph.maxLimit).toEqual(graph.maxLimit);
    });

    it('should update volume type when ctrl.volumeType changes', function() {
      var ctrl = createController();
      ctrl.volumeType = {name: 'spam'};
      $scope.$apply();

      expect(ctrl.volume.volume_type).toEqual('spam');
    });

    it('should set the validity of the volume size input field based on the limit', function() {
      getAbsoluteLimitsSpy.and.returnValue({
        success: function(callback) {
          return callback({
            maxTotalVolumeGigabytes: 2,
            totalVolumesUsed: 1,
            maxTotalVolumes: 5,
            totalGigabytesUsed: 1
          });
        }
      });

      var ctrl = createController();
      var graph = ctrl.storageQuota;
      var current = graph.data[0];
      var added = graph.data[1];

      ctrl.volume.size = 2;
      $scope.$apply();

      expect(current.value).toEqual(1);
      expect(added.value).toEqual(2);
      expect(graph.maxLimit).toEqual(2);
      expect(graph.overMax).toBeTruthy();
      expect($scope.volumeForm.$setValidity.calls.argsFor(1)).toEqual(['volumeSize', false]);
    });

    it('should deregister the storage watcher when the destroy event is thrown', function() {
      getAbsoluteLimitsSpy.and.returnValue({
        success: function(callback) {
          return callback({
            maxTotalVolumeGigabytes: 2,
            totalVolumesUsed: 1,
            maxTotalVolumes: 5,
            totalGigabytesUsed: 1
          });
        }
      });

      var ctrl = createController();
      var graph = ctrl.storageQuota;
      var current = graph.data[0];
      var added = graph.data[1];
      var remaining = graph.data[2];

      $scope.$emit('$destroy');

      ctrl.volume.size = 2;
      $scope.$apply();

      expect(current.value).toEqual(1);
      expect(added.value).toEqual(1);
      expect(remaining.value).toEqual(0);
      expect(graph.label).toEqual('100%');
      expect(graph.maxLimit).toEqual(2);
      expect(graph.overMax).toBeFalsy();
    });

    it('should deregister the volume type watcher when the destroy event is thrown', function() {
      var ctrl = createController();

      $scope.$emit('$destroy');
      $scope.$emit.calls.reset();

      ctrl.volumeType = {name: 'spam'};
      $scope.$apply();

      expect($scope.$emit).not.toHaveBeenCalled();
    });

    it('not default the availability_zone if none present', function() {

      cinder.getAvailabilityZones = function() {
        return {
          success: function(callback) {
            return callback({ items: [] });
          }
        };
      };
      var ctrl = createController();
      $scope.$apply();

      ctrl.volume.size = 100;
      expect(ctrl.volume.availability_zone).toEqual('');
    });

    it('should not update the graph if wrong values are given for volume size', function () {
      getAbsoluteLimitsSpy.and.returnValue({
        success: function(callback) {
          return callback({
            maxTotalVolumeGigabytes: 2,
            totalVolumesUsed: 1,
            maxTotalVolumes: 5,
            totalGigabytesUsed: 1
          });
        }
      });

      var ctrl = createController();
      expect(ctrl.volume.size).toBe(1);

      var graph = ctrl.storageQuota;
      var current = graph.data[0];
      var added = graph.data[1];
      var remaining = graph.data[2];

      expect(current.value).toEqual(1);
      expect(added.value).toEqual(1);
      expect(remaining.value).toEqual(0);
      expect(graph.label).toEqual('100%');
      expect(graph.maxLimit).toEqual(2);
      expect(graph.overMax).toBeFalsy();

      ctrl.volume.size = -5;
      $scope.$apply();

      expect(current.value).toEqual(1);
      expect(added.value).toEqual(1);
      expect(remaining.value).toEqual(0);
      expect(graph.label).toEqual('100%');
      expect(graph.maxLimit).toEqual(2);
      expect(graph.overMax).toBeFalsy();
    });
  });
})();
