/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

  describe('Launch Instance Source Step', function() {
    var noop = angular.noop;

    beforeEach(module('horizon.dashboard.project'));

    describe('LaunchInstanceSourceController', function() {
      var scope, ctrl, $browser, deferred;

      beforeEach(module(function($provide) {
        $provide.value('horizon.dashboard.project.workflow.launch-instance.boot-source-types', noop);
        $provide.value('bytesFilter', noop);
        $provide.value('horizon.framework.widgets.charts.donutChartSettings', noop);
        $provide.value('dateFilter', noop);
        $provide.value('decodeFilter', noop);
        $provide.value('gbFilter', noop);
        $provide.value('horizon.framework.widgets.charts.quotaChartDefaults', noop);
        $provide.value('horizon.dashboard.project.workflow.launch-instance.basePath', '');
      }));

      beforeEach(inject(function($controller, $rootScope, _$browser_, $q) {
        scope = $rootScope.$new();
        $browser = _$browser_;
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
            totalInstancesUsed: 0
          }
        };

        scope.launchInstanceSourceForm = {
          'boot-source-type': { $setValidity: noop }
        };

        ctrl = $controller('LaunchInstanceSourceController', { $scope: scope });

        scope.$apply();
      }));


      it('should be defined', function() {
        expect(ctrl).toBeDefined();
      });

      it('has defined error messages for invalid fields', function() {
        expect(ctrl.bootSourceTypeError).toBeDefined();
        expect(ctrl.instanceNameError).toBeDefined();
        expect(ctrl.instanceCountError).toBeDefined();
        expect(ctrl.volumeSizeError).toBeDefined();
      });

      it('defines the correct boot source options', function() {
        expect(ctrl.bootSourcesOptions).toBeDefined();
        var types = ['image', 'snapshot', 'volume', 'volume_snapshot'];
        var opts = ctrl.bootSourcesOptions.map(function(x) { return x.type; });
        types.forEach(function(key) {
          expect(opts).toContain(key);
        });
        expect(ctrl.bootSourcesOptions.length).toBe(types.length);
      });

      it('initializes transfer table variables', function() {
        // NOTE: these are set by the default, not the initial values.
        // Arguably we shouldn't even set the original values.
        expect(ctrl.tableHeadCells).toBeDefined();
        expect(ctrl.tableHeadCells.length).toEqual(5);
        expect(ctrl.tableBodyCells).toBeDefined();
        expect(ctrl.tableBodyCells.length).toEqual(5);
        expect(ctrl.tableData).toBeDefined();
        expect(Object.keys(ctrl.tableData).length).toEqual(4);
        expect(ctrl.helpText).toBeDefined();
        expect(ctrl.helpText.noneAllocText).toBeDefined();
        expect(ctrl.helpText.availHelpText).toBeDefined();
      });

      it('initializes table data to reflect "image" selection', function() {
        var list = [ { id: 'image-1'}, { id: 'image-2' } ]; // Use scope's values.
        var sel = []; // None selected.

        expect(ctrl.tableData).toEqual({
          available: list,
          allocated: sel,
          displayedAvailable: list,
          displayedAllocated: sel
        });
      });

      it('defaults to first source type if none existing', function() {
        expect(scope.model.newInstanceSpec.source_type.type).toBe('image');
        expect(ctrl.currentBootSource).toBe('image');
      });

      it('defaults source to image-2 if launchContext.imageId = image-2', function() {
        scope.launchContext = { imageId: 'image-2' };
        deferred.resolve();

        $browser.defer.flush();

        expect(ctrl.tableData.allocated[0]).toEqual({ id: 'image-2' });
        expect(scope.model.newInstanceSpec.source_type.type).toBe('image');
        expect(ctrl.currentBootSource).toBe('image');
      });

      describe('Scope Functions', function() {

        describe('updateBootSourceSelection', function() {
          var tableKeys = ['available', 'allocated',
            'displayedAvailable', 'displayedAllocated'];

          it('updates the scope appropriately', function() {
            var selSource = 'image';
            ctrl.updateBootSourceSelection(selSource);

            expect(ctrl.currentBootSource).toEqual('image');
            expect(scope.model.newInstanceSpec.vol_create).toBe(false);
            expect(scope.model.newInstanceSpec.vol_delete_on_terminate).toBe(false);

            // check table data
            expect(ctrl.tableData).toBeDefined();
            expect(Object.keys(ctrl.tableData)).toEqual(tableKeys);
            expect(ctrl.tableHeadCells.length).toBeGreaterThan(0);
            expect(ctrl.tableBodyCells.length).toBeGreaterThan(0);

            expect(ctrl.maxInstanceCount).toBe(10);

            // check chart data and labels
            expect(ctrl.instanceStats.label).toBe('10%');
            expect(ctrl.instanceStats.data[0].value).toEqual(0);
            expect(ctrl.instanceStats.data[1].value).toEqual(1);
            expect(ctrl.instanceStats.data[2].value).toEqual(9);
          });
        });

        describe('novaLimits.totalInstancesUsed watcher', function() {

          it('should update maxInstanceCount when maxTotalInstances changes', function() {
            scope.model.novaLimits.maxTotalInstances = 9;
            scope.$apply();

            expect(ctrl.maxInstanceCount).toBe(9);

            // check chart data and labels
            expect(ctrl.instanceStats.label).toBe('11%');
            expect(ctrl.instanceStats.data[0].value).toEqual(0);
            expect(ctrl.instanceStats.data[1].value).toEqual(1);
            expect(ctrl.instanceStats.data[2].value).toEqual(8);
          });
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

        describe('the instanceStats chart is set up correctly', function() {

          it('chart should have a title of "Total Instances"', function() {
            expect(ctrl.instanceStats.title).toBe('Total Instances');
          });

          it('chart should have a maxLimit value defined', function() {
            expect(ctrl.instanceStats.maxLimit).toBeDefined();
          });

          it('instanceStats.overMax should get set to true if instance_count exceeds maxLimit',
            function() {
              ctrl.tableData.allocated.push({ name: 'image-1', size: 0, min_disk: 0 });
              scope.model.newInstanceSpec.instance_count = 11;
              scope.$apply();

              // check chart data and labels
              expect(ctrl.instanceStats.label).toBe('110%');
              expect(ctrl.instanceStats.data[0].value).toEqual(0);
              expect(ctrl.instanceStats.data[1].value).toEqual(11);
              expect(ctrl.instanceStats.data[2].value).toEqual(0);
              // check to ensure overMax
              expect(ctrl.instanceStats.overMax).toBe(true);
            }
          );
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

          it('should update chart stats if instance count = 2 and no source selected', function() {
            scope.model.newInstanceSpec.instance_count = 2;
            scope.$apply();

            // check chart data and labels
            expect(ctrl.instanceStats.label).toBe('20%');
            expect(ctrl.instanceStats.data[0].value).toEqual(0);
            expect(ctrl.instanceStats.data[1].value).toEqual(2);
            expect(ctrl.instanceStats.data[2].value).toEqual(8);
          });

          it('should update chart stats if instance count = 2 and source selected', function() {
            ctrl.tableData.allocated.push({ name: 'image-1', size: 0, min_disk: 0 });
            scope.model.newInstanceSpec.instance_count = 2;
            scope.$apply();

            // check chart data and labels
            expect(ctrl.instanceStats.label).toBe('20%');
            expect(ctrl.instanceStats.data[0].value).toEqual(0);
            expect(ctrl.instanceStats.data[1].value).toEqual(2);
            expect(ctrl.instanceStats.data[2].value).toEqual(8);
          });
        });

        describe('source allocation', function() {

          it('should update chart stats if source allocated', function() {
            ctrl.tableData.allocated.push({ name: 'image-1', size: 0, min_disk: 0 });
            scope.$apply();

            // check chart data and labels
            expect(ctrl.instanceStats.label).toBe('10%');
            expect(ctrl.instanceStats.data[0].value).toEqual(0);
            expect(ctrl.instanceStats.data[1].value).toEqual(1);
            expect(ctrl.instanceStats.data[2].value).toEqual(9);
          });

          it('should set minVolumeSize to 1 if source allocated and size = min_disk = 1GB',
            function() {
              ctrl.tableData.allocated.push({ name: 'image-1', size: 1000000000, min_disk: 1 });
              scope.$apply();

              expect(ctrl.minVolumeSize).toBe(1);
            }
          );

          it('should set minVolumeSize to 1 if source allocated and size = 1GB and min_disk = 0GB',
            function() {
              ctrl.tableData.allocated.push({ name: 'image-1', size: 1000000000, min_disk: 0 });
              scope.$apply();

              expect(ctrl.minVolumeSize).toBe(1);
            }
          );

          it('should set minVolumeSize to 2 if source allocated and size = 1GB and min_disk = 2GB',
            function() {
              ctrl.tableData.allocated.push({ name: 'image-1', size: 1000000000, min_disk: 2 });
              scope.$apply();

              expect(ctrl.minVolumeSize).toBe(2);
            }
          );

          it('should set minVolumeSize to 0 if source allocated and size = min_disk = 0',
            function() {
              ctrl.tableData.allocated.push({ name: 'image-1', size: 0, min_disk: 0 });
              scope.$apply();

              expect(ctrl.minVolumeSize).toBe(0);
            }
          );

          it('should set minVolumeSize to 2 if source allocated and size = 1.5GB and min_disk = 0',
            function() {
              ctrl.tableData.allocated.push({ name: 'image-1', size: 1500000000, min_disk: 0 });
              scope.$apply();

              // minVolumeSize should use Math.ceil()
              expect(ctrl.minVolumeSize).toBe(2);
            }
          );

          it('should set minVolumeSize to undefined if boot source is not image', function() {
            var selSource = 'volume';
            ctrl.updateBootSourceSelection(selSource);

            expect(ctrl.currentBootSource).toEqual('volume');
            scope.$apply();

            expect(ctrl.minVolumeSize).toBeUndefined();
          });
        });
      });
    });

    describe('diskFormatFilter', function() {
      var diskFormatFilter;

      beforeEach(inject(function(_diskFormatFilter_) {
        diskFormatFilter = _diskFormatFilter_;
      }));

      describe('diskFormat', function() {

        it("returns 'FORMAT' if given 'format' in value", function() {
          expect(diskFormatFilter({ disk_format: 'format' })).toBe('FORMAT');
        });

        it("returns empty string if given null input", function() {
          expect(diskFormatFilter(null)).toBe('');
        });

        it("returns empty string if given input is empty object", function() {
          expect(diskFormatFilter({})).toBe('');
        });
      });
    });
  });

})();
