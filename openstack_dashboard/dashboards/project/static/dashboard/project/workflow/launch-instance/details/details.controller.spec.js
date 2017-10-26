/*
 * Copyright 2015 Hewlett Packard Enterprise Development Company LP
 *    (c) Copyright 2015 ThoughtWorks Inc.
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

  describe('Launch Instance Details Step', function() {
    var noop = angular.noop;

    beforeEach(module('horizon.dashboard.project'));

    describe('LaunchInstanceDetailsController', function() {
      var $q, scope, ctrl, deferred;
      var novaAPI = {
        isFeatureSupported: function() {
          var deferred = $q.defer();
          deferred.resolve({ data: true });
          return deferred.promise;
        }
      };

      beforeEach(module(function($provide) {
        $provide.value('horizon.framework.widgets.charts.donutChartSettings', noop);
        $provide.value('horizon.framework.widgets.charts.quotaChartDefaults', noop);
        $provide.value('horizon.app.core.openstack-service-api.nova', novaAPI);
      }));

      beforeEach(inject(function($injector, $controller, _$q_, _$rootScope_) {
        scope = _$rootScope_.$new();
        $q = _$q_;
        deferred = $q.defer();
        scope.initPromise = deferred.promise;

        scope.model = {
          newInstanceSpec: { source: [], source_type: '' },
          images: [ { id: 'image-1' }, { id: 'image-2' } ],
          imageSnapshots: [],
          volumes: [],
          volumeSnapshots: [],
          novaLimits: {
            maxTotalInstances: 10,
            totalInstancesUsed: 1
          }
        };

        novaAPI = $injector.get('horizon.app.core.openstack-service-api.nova');
        ctrl = $controller('LaunchInstanceDetailsController', { $scope: scope });

        scope.$apply();
      }));

      it('should have isDescriptionSupported defined', function() {
        spyOn(novaAPI, 'isFeatureSupported').and.callFake(function () {
          var deferred = $q.defer();
          deferred.resolve({ data: true });
          return deferred.promise;
        });
        expect(ctrl.isDescriptionSupported).toBe(true);
      });

      it('should define error messages for invalid fields', function() {
        expect(ctrl.instanceNameError).toBeDefined();
        expect(ctrl.instanceCountError).toBeDefined();
      });

      it('should update chart on creation', function() {
        var totalInstancesUsed = ctrl.instanceStats.data[0].value;
        var totalInstancesAdded = ctrl.instanceStats.data[1].value;
        var totalInstancesRemaining = ctrl.instanceStats.data[2].value;

        expect(totalInstancesUsed).toEqual(1);
        expect(totalInstancesAdded).toEqual(1);
        expect(totalInstancesRemaining).toEqual(8);
      });

      it('should update maximum instance creation limit on initialization', function() {
        expect(ctrl.maxInstanceCount).toEqual(9);
      });

      describe('novaLimits.maxTotalInstances watcher', function() {

        it('should update maxInstanceCount when maxTotalInstances changes', function() {
          scope.model.novaLimits.maxTotalInstances = 9;
          scope.$apply();

          expect(ctrl.maxInstanceCount).toBe(8);

          // check chart data and labels
          var totalInstancesUsed = ctrl.instanceStats.data[0].value;
          var totalInstancesAdded = ctrl.instanceStats.data[1].value;
          var totalInstancesRemaining = ctrl.instanceStats.data[2].value;

          expect(ctrl.instanceStats.label).toBe('22%');
          expect(totalInstancesUsed).toEqual(1);
          expect(totalInstancesAdded).toEqual(1);
          expect(totalInstancesRemaining).toEqual(7);
        });

        it('should update maxInstances when maxTotaInstances changes', function() {
          scope.model.novaLimits.maxTotalInstances = 9;
          scope.$apply();

          expect(ctrl.maxInstances).toBe(9);
          expect(ctrl.instanceStats.maxLimit).toEqual(9);
        });
      });

      describe('instanceCount watcher', function() {

        it('should reset instance count to 1 if instance count set to 0', function() {
          scope.model.newInstanceSpec.instance_count = 0;
          scope.$apply();

          expect(scope.model.newInstanceSpec.instance_count).toBe(1);
        });

        it('should reset instance count to 1 if instance count set to -1', function() {
          scope.model.newInstanceSpec.instance_count = -1;
          scope.$apply();

          expect(scope.model.newInstanceSpec.instance_count).toBe(1);
        });

        it('should update chart stats if instance count = 2', function() {
          scope.model.newInstanceSpec.instance_count = 2;
          scope.$apply();

          // check chart data and labels
          var totalInstancesUsed = ctrl.instanceStats.data[0].value;
          var totalInstancesAdded = ctrl.instanceStats.data[1].value;
          var totalInstancesRemaining = ctrl.instanceStats.data[2].value;

          expect(ctrl.instanceStats.label).toBe('30%');
          expect(totalInstancesUsed).toEqual(1);
          expect(totalInstancesAdded).toEqual(2);
          expect(totalInstancesRemaining).toEqual(7);
        });
      });

      describe('the instanceStats chart is set up correctly', function() {

        it('chart should have a title of "Total Instances"', function() {
          expect(ctrl.instanceStats.title).toBe('Total Instances');
        });

        it('chart should have a maxLimit value defined', function() {
          expect(ctrl.instanceStats.maxLimit).toBeDefined();
        });

        it('instanceStats.overMax should get set to true if instance_count exceeds maxLimit',
          function() {
            scope.model.newInstanceSpec.instance_count = 11;
            scope.$apply();

            // check chart data and labels
            var totalInstancesUsed = ctrl.instanceStats.data[0].value;
            var totalInstancesAdded = ctrl.instanceStats.data[1].value;
            var totalInstancesRemaining = ctrl.instanceStats.data[2].value;

            expect(ctrl.instanceStats.label).toBe('120%');
            expect(totalInstancesUsed).toEqual(1);
            expect(totalInstancesAdded).toEqual(11);
            expect(totalInstancesRemaining).toEqual(0);

            // check to ensure overMax
            expect(ctrl.instanceStats.overMax).toBe(true);
          }
        );
      });

      describe('novaLimits.totalInstancesUsed watcher', function() {

        it('should update chart stats when totalInstancesUsed changes', function() {
          scope.model.novaLimits.totalInstancesUsed = 1;
          scope.$apply();

          expect(ctrl.maxInstanceCount).toBe(9);

          // check chart data and labels
          expect(ctrl.instanceStats.label).toBe('20%');
          expect(ctrl.instanceStats.data[0].value).toEqual(1);
          expect(ctrl.instanceStats.data[1].value).toEqual(1);
          expect(ctrl.instanceStats.data[2].value).toEqual(8);
        });
      });

    });
  });
})();
