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
    beforeEach(module('horizon.framework'));

    describe('LaunchInstanceSourceController', function() {
      var scope, ctrl, $browser, deferred;

      beforeEach(module(function($provide) {
        $provide.value(
          'horizon.dashboard.project.workflow.launch-instance.boot-source-types', noop
        );
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
        spyOn(scope, '$watch').and.callThrough();
        spyOn(scope, '$watchCollection').and.callThrough();
        $browser = _$browser_;
        deferred = $q.defer();
        scope.initPromise = deferred.promise;

        scope.model = {
          newInstanceSpec: { source: [], source_type: '' },
          images: [ { id: 'image-1' }, { id: 'image-2' } ],
          imageSnapshots: [],
          volumes: [ { id: 'volume-1' }, { id: 'volume-2' } ],
          volumeSnapshots: [ {id: 'snapshot-2'} ],
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
        expect(ctrl.volumeSizeError).toBeDefined();
      });

      it('defines the correct boot source options', function() {
        expect(ctrl.bootSourcesOptions).toBeDefined();
        var types = ['image', 'snapshot', 'volume', 'volume_snapshot'];
        var opts = ctrl.bootSourcesOptions.map(function(x) {
          return x.type;
        });
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

      describe('facets', function() {
        it('should set facets for search by default', function() {
          expect(ctrl.sourceFacets).toBeDefined();

          expect(ctrl.sourceFacets.length).toEqual(5);
          expect(ctrl.sourceFacets[0].name).toEqual('name');
          expect(ctrl.sourceFacets[1].name).toEqual('updated_at');
          expect(ctrl.sourceFacets[2].name).toEqual('size');
          expect(ctrl.sourceFacets[3].name).toEqual('disk_format');
          expect(ctrl.sourceFacets[4].name).toEqual('is_public');
        });

        it('should broadcast event when source type is changed', function() {
          spyOn(scope, '$broadcast').and.callThrough();
          ctrl.updateBootSourceSelection('volume');
          ctrl.updateBootSourceSelection('snapshot');
          expect(scope.$broadcast).toHaveBeenCalledWith('facetsChanged');
        });

        it('should change facets for snapshot source type', function() {
          expect(ctrl.sourceFacets).toBeDefined();

          ctrl.updateBootSourceSelection('snapshot');

          expect(ctrl.sourceFacets.length).toEqual(5);
          expect(ctrl.sourceFacets[0].name).toEqual('name');
          expect(ctrl.sourceFacets[1].name).toEqual('updated_at');
          expect(ctrl.sourceFacets[2].name).toEqual('size');
          expect(ctrl.sourceFacets[3].name).toEqual('disk_format');
          expect(ctrl.sourceFacets[4].name).toEqual('is_public');
        });

        it('should change facets for volume source type', function() {
          expect(ctrl.sourceFacets).toBeDefined();

          ctrl.updateBootSourceSelection('volume');

          expect(ctrl.sourceFacets.length).toEqual(5);
          expect(ctrl.sourceFacets[0].name).toEqual('name');
          expect(ctrl.sourceFacets[1].name).toEqual('description');
          expect(ctrl.sourceFacets[2].name).toEqual('size');
          expect(ctrl.sourceFacets[3].name).toEqual('volume_image_metadata.disk_format');
          expect(ctrl.sourceFacets[4].name).toEqual('encrypted');
        });

        it('should change facets for volume_snapshot source type', function() {
          expect(ctrl.sourceFacets).toBeDefined();

          ctrl.updateBootSourceSelection('volume_snapshot');

          expect(ctrl.sourceFacets.length).toEqual(5);
          expect(ctrl.sourceFacets[0].name).toEqual('name');
          expect(ctrl.sourceFacets[1].name).toEqual('description');
          expect(ctrl.sourceFacets[2].name).toEqual('size');
          expect(ctrl.sourceFacets[3].name).toEqual('created_at');
          expect(ctrl.sourceFacets[4].name).toEqual('status');
        });
      });

      it('defaults source to volume-2 if launchContext.volumeId = volume-2', function() {
        scope.launchContext = { volumeId: 'volume-2' };
        deferred.resolve();

        $browser.defer.flush();

        expect(ctrl.tableData.allocated[0]).toEqual({ id: 'volume-2' });
        expect(scope.model.newInstanceSpec.source_type.type).toBe('volume');
        expect(ctrl.currentBootSource).toBe('volume');
      });

      it('defaults source to snapshot-2 if launchContext.snapshotId = snapshot-2', function() {
        scope.launchContext = { snapshotId: 'snapshot-2' };
        deferred.resolve();

        $browser.defer.flush();

        expect(ctrl.tableData.allocated[0]).toEqual({ id: 'snapshot-2' });
        expect(scope.model.newInstanceSpec.source_type.type).toBe('volume_snapshot');
        expect(ctrl.currentBootSource).toBe('volume_snapshot');
      });

      describe('Scope Functions', function() {

        describe('watchers', function () {
          it('establishes five watches', function() {
            expect(scope.$watch.calls.count()).toBe(6);
          });

          it("establishes two watch collections", function () {
            expect(scope.$watchCollection.calls.count()).toBe(3);
          });
        });

        describe('updateBootSourceSelection', function() {
          var tableKeys = ['available', 'allocated',
            'displayedAvailable', 'displayedAllocated'];

          it('updates the scope appropriately', function() {
            var selSource = 'image';
            ctrl.updateBootSourceSelection(selSource);

            expect(ctrl.currentBootSource).toEqual('image');
            expect(scope.model.newInstanceSpec.vol_create).toBe(true);
            expect(scope.model.newInstanceSpec.vol_delete_on_instance_delete).toBe(false);

            // check table data
            expect(ctrl.tableData).toBeDefined();
            expect(Object.keys(ctrl.tableData)).toEqual(tableKeys);
            expect(ctrl.tableHeadCells.length).toBeGreaterThan(0);
            expect(ctrl.tableBodyCells.length).toBeGreaterThan(0);
          });

          it('should broadcast event when boot source changes', function() {
            spyOn(scope, '$broadcast');
            scope.$apply();

            var selSource = 'volume';
            ctrl.updateBootSourceSelection(selSource);
            expect(ctrl.currentBootSource).toEqual('volume');

            scope.$apply();
            expect(scope.$broadcast).toHaveBeenCalled();
          });
        });

        describe('source allocation', function() {

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

          it('should set minVolumeSize to 0 if boot source is not image', function() {
            var selSource = 'volume';
            ctrl.updateBootSourceSelection(selSource);

            expect(ctrl.currentBootSource).toEqual('volume');
            scope.$apply();

            expect(ctrl.minVolumeSize).toBe(0);
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

        it("returns 'format' if given 'format' in value", function() {
          expect(diskFormatFilter({ disk_format: 'format' })).toBe('format');
        });

        it("returns empty string if given null input", function() {
          expect(diskFormatFilter(null)).toBe('');
        });

        it("returns empty string if given input is empty object", function() {
          expect(diskFormatFilter({})).toBe('');
        });

        it("returns 'docker' if container format is docker and disk format is raw", function() {
          expect(diskFormatFilter({disk_format: 'raw', container_format: 'docker'})).toBe('docker');
          expect(diskFormatFilter({disk_format: 'ami', container_format: 'docker'})).toBe('ami');
          expect(diskFormatFilter({disk_format: 'raw', container_format: 'raw'})).toBe('raw');
          expect(diskFormatFilter({disk_format: 'raw', container_format: null})).toBe('raw');
        });
      });
    });
  });

})();
