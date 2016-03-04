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
(function () {
  'use strict';

  describe('Launch Instance Flavor Step', function () {
    describe('LaunchInstanceFlavorController', function () {
      var ctrl, scope, model, defaults;

      beforeEach(module('horizon.dashboard.project.workflow.launch-instance'));

      beforeEach(inject(function ($controller, $rootScope) {
        scope = $rootScope.$new();

        // Track calls to $watch and $watchCollection, and let them
        // do their real work to register watch listeners. Remember
        // that $watchCollection makes its own call to $watch.
        spyOn(scope, '$watch').and.callThrough();
        spyOn(scope, '$watchCollection').and.callThrough();

        scope.launchInstanceFlavorForm = {'allocated-flavor': {}};

        model = { newInstanceSpec: { },
                  novaLimits: { },
                  flavors: []
                };
        defaults = { usageLabel: "label",
                     usageColorClass: "class1",
                     addedLabel: "label2",
                     addedColorClass: "class2",
                     remainingLabel: "label3",
                     remainingColorClass: "class3"
                   };

        ctrl = $controller('LaunchInstanceFlavorController as selectFlavorCtrl',
                           { $scope:scope,
                             'horizon.framework.widgets.charts.quotaChartDefaults': defaults,
                             launchInstanceModel: model });
      }));

      it('defines expected labels', function () {
        var props = [
          'chartTotalInstancesLabel',
          'chartTotalVcpusLabel', 'chartTotalRamLabel'
        ];

        props.forEach(function (prop) {
          expect(ctrl[prop]).toBeDefined();
          expect(angular.isString(ctrl[prop]));
        });
      });

      it('has a chart data function that returns expected values', function () {
        var data = ctrl.getChartData('fakeTitle', 1, 2, 3);

        expect(data.title).toBe('fakeTitle');
        expect(data.label).toBe('100%');
        data.data.forEach(function (cData) {
          expect(angular.isString(cData.label));
          expect(angular.isNumber(cData.value));
          expect(angular.isString(cData.color));
        });
      });

      describe("watches", function () {

        beforeEach( function() {
          // Mock out calls made by the watch listeners to minimize
          // the amount of mock data needed to successfully trigger
          // a watch listener
          spyOn(ctrl, 'updateFlavorFacades').and.returnValue();
          spyOn(ctrl, 'validateFlavor').and.returnValue();

          // Initialize the watchers with default data
          scope.$apply();

          // Reset the spies now that we have initialized the watchers
          // so that tests don't see the calls made during setup
          ctrl.updateFlavorFacades.calls.reset();
          ctrl.validateFlavor.calls.reset();
        });

        it("establishes five watches", function () {
          // Count calls to $watch (note: $watchCollection
          // also calls $watch)
          expect(scope.$watch.calls.count()).toBe(5);
        });

        it("establishes three watch collections", function () {
          expect(scope.$watchCollection.calls.count()).toBe(3);
        });

        describe("novaLimits watch", function () {

          it("sets the control novaLimits", function () {
            model.novaLimits = "new";
            scope.$apply();
            expect(ctrl.novaLimits).toBe('new');
          });

          it("calls updateFlavorFacades()", function () {
            model.novaLimits = "new";
            scope.$apply();
            expect(ctrl.updateFlavorFacades.calls.count()).toBe(1);
          });
        });

        describe("instance count watch", function () {

          it("sets the control instanceCount when 1 or more", function () {
            model.newInstanceSpec.instance_count = 5;
            scope.$apply();
            expect(ctrl.instanceCount).toBe(5);
          });

          it("sets the control instanceCount to 1 when less than 1", function () {
            model.newInstanceSpec.instance_count = 0;
            scope.$apply();
            expect(ctrl.instanceCount).toBe(1);
          });

          it("does nothing when new value is not defined", function () {
            delete model.newInstanceSpec.instance_count;
            scope.$apply();
            expect(ctrl.instanceCount).toBe(1);
            expect(ctrl.updateFlavorFacades).not.toHaveBeenCalled();
            expect(ctrl.validateFlavor).not.toHaveBeenCalled();
          });

          it("calls updateFlavorFacades()", function () {
            model.newInstanceSpec.instance_count = 5;
            scope.$apply();
            expect(ctrl.updateFlavorFacades.calls.count()).toBe(1);
          });

          it("calls validateFlavor()", function () {
            model.newInstanceSpec.instance_count = 5;
            scope.$apply();
            expect(ctrl.validateFlavor.calls.count()).toBe(1);
          });
        });

        describe("model.flavors", function () {

          it("sets the control flavors", function () {
            model.flavors = "new";
            scope.$apply();
            expect(ctrl.flavors).toBe("new");
          });

          it("calls updateFlavorFacades", function () {
            model.flavors = "new";
            scope.$apply();
            expect(ctrl.updateFlavorFacades.calls.count()).toBe(1);
          });
        });

        describe("selectFlavorCtrl.allocatedFlavorFacades", function () {

          it("deletes flavor if falsy facade", function () {
            model.newInstanceSpec.flavor = "to be removed";
            ctrl.allocatedFlavorFacades = false;
            scope.$apply();
            expect(model.newInstanceSpec.flavor).not.toBeDefined();
          });

          it("deletes flavor if empty facade", function () {
            // First set a non-empty allocated facade
            ctrl.allocatedFlavorFacades = [{flavor: "non-empty", enabled: "true"}];
            scope.$apply();
            expect(model.newInstanceSpec.flavor).toBe("non-empty");

            // Now set the empty allocated facade and prove that the flavor is
            // cleaned up.
            model.newInstanceSpec.flavor = "to be removed";
            ctrl.allocatedFlavorFacades = [];
            scope.$apply();
            expect(model.newInstanceSpec.flavor).not.toBeDefined();
          });

          it("sets the model's flavor", function () {
            ctrl.allocatedFlavorFacades = [{flavor: "raspberry", enabled: "true"}];
            scope.$apply();
            expect(model.newInstanceSpec.flavor).toEqual("raspberry");
          });

          it("calls validateFlavor", function () {
            ctrl.allocatedFlavorFacades = [{flavor: "non-empty", enabled: "true"}];
            scope.$apply();
            expect(ctrl.validateFlavor.calls.count()).toBe(1);
          });
        });

        describe("instance spec source changes", function () {

          it("sets the source", function () {
            model.newInstanceSpec.source = ["new"];
            scope.$apply();
            expect(ctrl.source).toBe("new");
          });

          it("sets the source to null if not provided", function () {
            model.newInstanceSpec.source = ["new"];
            scope.$apply();
            expect(ctrl.source).toBe("new");

            delete model.newInstanceSpec.source;
            scope.$apply();
            expect(ctrl.source).toBeNull();
          });

          it("sets the source to null if not an array", function () {
            model.newInstanceSpec.source = ["new"];
            scope.$apply();
            expect(ctrl.source).toBe("new");

            model.newInstanceSpec.source = 1;
            scope.$apply();
            expect(ctrl.source).toBeNull();
          });

          it("calls updateFlavorFacades", function () {
            model.newInstanceSpec.source = ["new"];
            scope.$apply();
            expect(ctrl.updateFlavorFacades.calls.count()).toBe(1);
          });

          it("calls validateFlavor", function () {
            model.newInstanceSpec.source = ["new"];
            scope.$apply();
            expect(ctrl.validateFlavor.calls.count()).toBe(1);
          });
        });

      });

      describe("when having allocated flavors", function () {
        beforeEach(function () {
          ctrl.allocatedFlavorFacades = [{enabled: true}];
          scope.launchInstanceFlavorForm['allocated-flavor'] = { $setValidity: function () {} };
          spyOn(scope.launchInstanceFlavorForm['allocated-flavor'], "$setValidity");
        });
        describe("and you call #validateFlavor", function () {
          it("marks the flavor as validated", function () {
            ctrl.validateFlavor();
            expect(scope.launchInstanceFlavorForm['allocated-flavor']
              .$setValidity).toHaveBeenCalledWith('flavor', true);
          });
        });
      });

      describe("when not having allocated flavors", function () {
        beforeEach(function () {
          scope.launchInstanceFlavorForm['allocated-flavor'] = { $setValidity: function () {} };
          spyOn(scope.launchInstanceFlavorForm['allocated-flavor'], "$setValidity");
        });
        describe("and you call #validateFlavor", function () {
          it("does not mark the flavor validated", function () {
            ctrl.validateFlavor();
            expect(scope.launchInstanceFlavorForm['allocated-flavor']
              .$setValidity).not.toHaveBeenCalled();
          });
        });
      });

      describe("when having flavors defined", function () {
        beforeEach(function () {
          ctrl.flavors = [{name: "flava"}];
        });
        describe("and #buildFlavorFacades", function () {
          it("creates one facade for each flavor entry", function () {
            ctrl.buildFlavorFacades();
            expect(ctrl.availableFlavorFacades.length).toBe(1);
          });
        });
      });

      describe("when having no flavors defined", function () {
        describe("and #buildFlavorFacades", function () {
          it("creates no facades", function () {
            ctrl.buildFlavorFacades();
            expect(ctrl.availableFlavorFacades.length).toBe(0);
          });
        });
      });

      describe("when flavor definitions change", function () {
        beforeEach(function () {
          ctrl.flavors = [{name: "flava"}];
        });
        describe("and #updateFlavorFacades", function () {
          it("creates no facades", function () {
            ctrl.updateFlavorFacades();
            expect(ctrl.availableFlavorFacades.length).toBe(1);
          });
        });
      });

      describe("when checking a flavor for errors", function () {
        beforeEach(function () {
          ctrl.flavors = [{
            name: "flava",
            vcpus: "1",
            ram: 50,
            disk: 50
          }];
          ctrl.source = { min_disk:100, min_ram:100};
          model.newInstanceSpec.source_type = {type: 'image'};
        });
        describe("and there are no cpus available", function () {
          it("presents a vcpu error message", function () {
            expect(ctrl.getErrors(ctrl.flavors[0]).vcpus).toBeDefined();
          });
        });
        describe("and there is not sufficient ram available", function () {
          it("presents a ram error message", function () {
            expect(ctrl.getErrors(ctrl.flavors[0]).ram).toBeDefined();
          });
        });
        describe("and the image source requires more disk available", function () {
          it("presents a disk error message", function () {
            expect(ctrl.getErrors(ctrl.flavors[0]).disk).toBeDefined();
          });
        });

        describe("when min disk is less than zero", function () {

          beforeEach(function () {
            ctrl.flavors = [{
              name: "flava",
              vcpus: "1",
              ram: 0, // Modified so doesn't trip other error messages.
              disk: 50
            }];
            ctrl.source = { min_disk:-1, min_ram:-1};
          });

          it("doesn't create disk errors", function () {
            expect(ctrl.getErrors(ctrl.flavors[0]).disk).not.toBeDefined();
          });

          it("doesn't create ram errors", function () {
            expect(ctrl.getErrors(ctrl.flavors[0]).ram).not.toBeDefined();
          });

        });
      });

      it('initializes empty facades', function () {
        expect(ctrl.availableFlavorFacades).toEqual([]);
        expect(ctrl.displayedAvailableFlavorFacades).toEqual([]);
        expect(ctrl.allocatedFlavorFacades).toEqual([]);
        expect(ctrl.displayedAllocatedFlavorFacades).toEqual([]);
      });

      it('initializes empty flavors', function () {
        expect(ctrl.flavors).toEqual([]);
      });

      it('initializes nova limits', function () {
        expect(ctrl.novaLimits).toEqual({});
      });

      it('initializes instance count to 1', function () {
        expect(ctrl.instanceCount).toBe(1);
      });

      it('initializes transfer table model', function () {
        expect(ctrl.transferTableModel).toBeDefined();
        var mod = ctrl.transferTableModel;
        expect(mod.allocated).toBe(ctrl.allocatedFlavorFacades);
        expect(mod.displayedAllocated).toBe(ctrl.displayedAllocatedFlavorFacades);
        expect(mod.available).toBe(ctrl.availableFlavorFacades);
        expect(mod.displayedAvailable).toBe(ctrl.displayedAvailableFlavorFacades);
        expect(Object.keys(mod).length).toBe(4);
      });

      it('initializes chart data', function () {
        expect(ctrl.instancesChartData).toEqual({});
      });

      it('allows only one allocation', function () {
        expect(ctrl.allocationLimits).toBeDefined();
        expect(ctrl.allocationLimits.maxAllocation).toBe(1);
      });

      describe('Functions', function () {
        describe('defaultIfUndefined', function () {

          it('returns the given default if value is undefined', function () {
            /*eslint-disable no-undefined */
            expect(ctrl.defaultIfUndefined(undefined, 'defValue')).toBe('defValue');
            /*eslint-enable no-undefined */
          });

          it('returns the value if defined', function () {
            expect(ctrl.defaultIfUndefined('myVal', 'defValue')).toBe('myVal');
          });
        });
      });

    });

  });

})();
