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

    beforeEach(module('hz.dashboard.launch-instance'));

    describe('LaunchInstanceSourceCtrl', function() {
      var scope, ctrl, $browser, deferred;

      beforeEach(module(function($provide) {
        $provide.value('bootSourceTypes', noop);
        $provide.value('bytesFilter', noop);
        $provide.value('horizon.framework.widgets.charts.donutChartSettings', noop);
        $provide.value('dateFilter', noop);
        $provide.value('decodeFilter', noop);
        $provide.value('gbFilter', noop);
        $provide.value('horizon.framework.widgets.charts.quotaChartDefaults', noop);
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

        ctrl = $controller('LaunchInstanceSourceCtrl', { $scope: scope });

        scope.$digest();
      }));

      it('has its own labels', function() {
        expect(scope.label).toBeDefined();
        expect(Object.keys(scope.label).length).toBeGreaterThan(0);
      });

      it('has defined error messages for invalid fields', function() {
        expect(scope.bootSourceTypeError).toBeDefined();
        expect(scope.instanceNameError).toBeDefined();
        expect(scope.instanceCountError).toBeDefined();
        expect(scope.volumeSizeError).toBeDefined();
      });

      it('defines the correct boot source options', function() {
        expect(scope.bootSourcesOptions).toBeDefined();
        var types = ['image', 'snapshot', 'volume', 'volume_snapshot'];
        var opts = scope.bootSourcesOptions.map(function(x) { return x.type; });
        types.forEach(function(key) {
          expect(opts).toContain(key);
        });
        expect(scope.bootSourcesOptions.length).toBe(types.length);
      });

      it('initializes transfer table variables', function() {
        // NOTE: these are set by the default, not the initial values.
        // Arguably we shouldn't even set the original values.
        expect(scope.tableHeadCells).toBeDefined();
        expect(scope.tableHeadCells.length).toEqual(5);
        expect(scope.tableBodyCells).toBeDefined();
        expect(scope.tableBodyCells.length).toEqual(5);
        expect(scope.tableData).toBeDefined();
        expect(Object.keys(scope.tableData).length).toEqual(4);
        // TODO really confused but the use of this helpText variable
        // in the code, esp. the use of extend, rather than just setting it
        // once.
        expect(scope.helpText).toBeDefined();
        expect(scope.helpText.noneAllocText).toBeDefined();
        expect(scope.helpText.availHelpText).toBeDefined();
      });

      it('initializes table data to reflect "image" selection', function() {
        var list = [ { id: 'image-1'}, { id: 'image-2' } ]; // Use scope's values.
        var sel = []; // None selected.

        expect(scope.tableData).toEqual({
          available: list,
          allocated: sel,
          displayedAvailable: list,
          displayedAllocated: sel
        });
      });

      it('defaults to first source type if none existing', function() {
        expect(scope.model.newInstanceSpec.source_type.type).toBe('image');
        expect(scope.currentBootSource).toBe('image');
      });

      it('defaults source to image-2 if launchContext.imageId = image-2', function() {
        scope.launchContext = { imageId: 'image-2' };
        deferred.resolve();

        $browser.defer.flush();

        expect(scope.tableData.allocated[0]).toEqual({ id: 'image-2' });
        expect(scope.model.newInstanceSpec.source_type.type).toBe('image');
        expect(scope.currentBootSource).toBe('image');
      });

      describe('Scope Functions', function() {

        describe('updateBootSourceSelection', function() {
          var tableKeys = ['available', 'allocated',
            'displayedAvailable', 'displayedAllocated'];

          it('updates the scope appropriately', function() {
            var selSource = 'image';
            scope.updateBootSourceSelection(selSource);

            expect(scope.currentBootSource).toEqual('image');
            expect(scope.model.newInstanceSpec.vol_create).toBe(false);
            expect(scope.model.newInstanceSpec.vol_delete_on_terminate).toBe(false);

            // check table data
            expect(scope.tableData).toBeDefined();
            expect(Object.keys(scope.tableData)).toEqual(tableKeys);
            expect(scope.tableHeadCells.length).toBeGreaterThan(0);
            expect(scope.tableBodyCells.length).toBeGreaterThan(0);

            expect(scope.maxInstanceCount).toBe(10);

            // check chart data and labels
            expect(scope.instanceStats.label).toBe('10%');
            expect(scope.instanceStats.data[0].value).toEqual(0);
            expect(scope.instanceStats.data[1].value).toEqual(1);
            expect(scope.instanceStats.data[2].value).toEqual(9);
          });
        });

        describe('novaLimits.totalInstancesUsed watcher', function() {

          it('should update maxInstanceCount when maxTotalInstances changes', function() {
            scope.model.novaLimits.maxTotalInstances = 9;
            scope.$digest();

            expect(scope.maxInstanceCount).toBe(9);

            // check chart data and labels
            expect(scope.instanceStats.label).toBe('11%');
            expect(scope.instanceStats.data[0].value).toEqual(0);
            expect(scope.instanceStats.data[1].value).toEqual(1);
            expect(scope.instanceStats.data[2].value).toEqual(8);
          });
        });

        describe('novaLimits.totalInstancesUsed watcher', function() {

          it('should update chart stats when totalInstancesUsed changes', function() {
            scope.model.novaLimits.totalInstancesUsed = 1;
            scope.$digest();

            expect(scope.maxInstanceCount).toBe(9);

            // check chart data and labels
            expect(scope.instanceStats.label).toBe('20%');
            expect(scope.instanceStats.data[0].value).toEqual(1);
            expect(scope.instanceStats.data[1].value).toEqual(1);
            expect(scope.instanceStats.data[2].value).toEqual(8);
          });
        });

        describe('the instanceStats chart is set up correctly', function() {

          it('chart should have a title of "Total Instances"', function() {
            expect(scope.instanceStats.title).toBe('Total Instances');
          });

          it('chart should have a maxLimit value defined', function() {
            expect(scope.instanceStats.maxLimit).toBeDefined();
          });

          it('instanceStats.overMax should get set to true if instance_count exceeds maxLimit',
            function() {
              scope.tableData.allocated.push({ name: 'image-1', size: 0, min_disk: 0 });
              scope.model.newInstanceSpec.instance_count = 11;
              scope.$digest();

              // check chart data and labels
              expect(scope.instanceStats.label).toBe('110%');
              expect(scope.instanceStats.data[0].value).toEqual(0);
              expect(scope.instanceStats.data[1].value).toEqual(11);
              expect(scope.instanceStats.data[2].value).toEqual(0);
              // check to ensure overMax
              expect(scope.instanceStats.overMax).toBe(true);
            }
          );
        });

        describe('instanceCount watcher', function() {

          it('should reset instance count to 1 if instance count set to 0', function() {
            scope.model.newInstanceSpec.instance_count = 0;
            scope.$digest();

            expect(scope.model.newInstanceSpec.instance_count).toBe(1);
          });

          it('should reset instance count to 1 if instance count set to -1', function() {
            scope.model.newInstanceSpec.instance_count = -1;
            scope.$digest();

            expect(scope.model.newInstanceSpec.instance_count).toBe(1);
          });

          it('should update chart stats if instance count = 2 and no source selected', function() {
            scope.model.newInstanceSpec.instance_count = 2;
            scope.$digest();

            // check chart data and labels
            expect(scope.instanceStats.label).toBe('20%');
            expect(scope.instanceStats.data[0].value).toEqual(0);
            expect(scope.instanceStats.data[1].value).toEqual(2);
            expect(scope.instanceStats.data[2].value).toEqual(8);
          });

          it('should update chart stats if instance count = 2 and source selected', function() {
            scope.tableData.allocated.push({ name: 'image-1', size: 0, min_disk: 0 });
            scope.model.newInstanceSpec.instance_count = 2;
            scope.$digest();

            // check chart data and labels
            expect(scope.instanceStats.label).toBe('20%');
            expect(scope.instanceStats.data[0].value).toEqual(0);
            expect(scope.instanceStats.data[1].value).toEqual(2);
            expect(scope.instanceStats.data[2].value).toEqual(8);
          });
        });

        describe('source allocation', function() {

          it('should update chart stats if source allocated', function() {
            scope.tableData.allocated.push({ name: 'image-1', size: 0, min_disk: 0 });
            scope.$digest();

            // check chart data and labels
            expect(scope.instanceStats.label).toBe('10%');
            expect(scope.instanceStats.data[0].value).toEqual(0);
            expect(scope.instanceStats.data[1].value).toEqual(1);
            expect(scope.instanceStats.data[2].value).toEqual(9);
          });

          it('should set minVolumeSize to 1 if source allocated and size = min_disk = 1GB',
            function() {
              scope.tableData.allocated.push({ name: 'image-1', size: 1000000000, min_disk: 1 });
              scope.$digest();

              expect(scope.minVolumeSize).toBe(1);
            }
          );

          it('should set minVolumeSize to 1 if source allocated and size = 1GB and min_disk = 0GB',
            function() {
              scope.tableData.allocated.push({ name: 'image-1', size: 1000000000, min_disk: 0 });
              scope.$digest();

              expect(scope.minVolumeSize).toBe(1);
            }
          );

          it('should set minVolumeSize to 2 if source allocated and size = 1GB and min_disk = 2GB',
            function() {
              scope.tableData.allocated.push({ name: 'image-1', size: 1000000000, min_disk: 2 });
              scope.$digest();

              expect(scope.minVolumeSize).toBe(2);
            }
          );

          it('should set minVolumeSize to 0 if source allocated and size = min_disk = 0',
            function() {
              scope.tableData.allocated.push({ name: 'image-1', size: 0, min_disk: 0 });
              scope.$digest();

              expect(scope.minVolumeSize).toBe(0);
            }
          );

          it('should set minVolumeSize to 2 if source allocated and size = 1.5GB and min_disk = 0',
            function() {
              scope.tableData.allocated.push({ name: 'image-1', size: 1500000000, min_disk: 0 });
              scope.$digest();

              // minVolumeSize should use Math.ceil()
              expect(scope.minVolumeSize).toBe(2);
            }
          );

          it('should set minVolumeSize to undefined if boot source is not image', function() {
            var selSource = 'volume';
            scope.updateBootSourceSelection(selSource);

            expect(scope.currentBootSource).toEqual('volume');
            scope.$digest();

            expect(scope.minVolumeSize).toBeUndefined();
          });
        });
      });
    });

    describe('LaunchInstanceSourceHelpCtrl', function() {
      var ctrl;

      beforeEach(inject(function($controller) {
        ctrl = $controller('LaunchInstanceSourceHelpCtrl', {});
      }));

      it('defines the title', function() {
        expect(ctrl.title).toBeDefined();
      });

      it('defines the instance details title', function() {
        expect(ctrl.title).toBeDefined();
      });

      it('has instance details paragraphs', function() {
        expect(ctrl.instanceDetailsParagraphs).toBeDefined();
        expect(ctrl.instanceDetailsParagraphs.length).toBeGreaterThan(0);
      });

      it('defines the instance source title', function() {
        expect(ctrl.instanceSourceTitle).toBeDefined();
      });

      it('has instance source paragraphs', function() {
        expect(ctrl.instanceSourceParagraphs).toBeDefined();
        expect(ctrl.instanceSourceParagraphs.length).toBeGreaterThan(0);
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
