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
    describe('LaunchInstanceFlavorCtrl', function () {
      var ctrl, scope, model, defaults;

      beforeEach(module('hz.dashboard.launch-instance'));

      beforeEach(inject(function ($controller) {
        scope = { $watch: function () {},
                  $watchCollection: function () {},
                  launchInstanceFlavorForm: {}
                };
        model = { newInstanceSpec: { instance_count: 1,
                                     flavor: {},
                                     source_type: { type: "image" },
                                     source: "source_value"},
                  novaLimits: { totalInstancesUsed: 10, maxTotalInstances: 3,
                                totalCoresUsed: 4, maxTotalCores: 10,
                                totalRAMUsed: 100, maxTotalRAMSize: 200 }
                };
        defaults = { usageLabel: "label",
                     usageColorClass: "class1",
                     addedLabel: "label2",
                     addedColorClass: "class2",
                     remainingLabel: "label3",
                     remainingColorClass: "class3"
                   };
        spyOn(scope, '$watch');
        spyOn(scope, '$watchCollection');
        ctrl = $controller('LaunchInstanceFlavorCtrl',
                           { $scope:scope,
                             'horizon.framework.widgets.charts.quotaChartDefaults': defaults,
                             launchInstanceModel: model });
      }));

      it('defines expected labels', function () {
        var props = [
          'title', 'subtitle', 'chartTotalInstancesLabel',
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

        it("establishes two watches", function () {
          expect(scope.$watch.calls.count()).toBe(2);
        });

        describe("novaLimits watch", function () {
          var watched, action;

          beforeEach(function () {
            // NOTE: This ordering of watches is fragile.
            watched = scope.$watch.calls.argsFor(0)[0]();
            action = scope.$watch.calls.argsFor(0)[1];
          });

          it("watches model.novaLimits", function () {
            // value as injected above.
            var novaLimits = { totalInstancesUsed: 10, maxTotalInstances: 3,
                                totalCoresUsed: 4, maxTotalCores: 10,
                                totalRAMUsed: 100, maxTotalRAMSize: 200 };
            expect(watched).toEqual(novaLimits);
          });

          it("sets the control novaLimits", function () {
            var myScope = {selectFlavorCtrl: ctrl};
            action('new', 'old', myScope);
            expect(ctrl.novaLimits).toBe('new');
          });

          it("calls updateFlavorFacades()", function () {
            var myScope = {selectFlavorCtrl: ctrl};
            spyOn(ctrl, 'updateFlavorFacades');
            action('na', 'na', myScope);
            expect(ctrl.updateFlavorFacades).toHaveBeenCalledWith();
          });
        });

        describe("instance count watch", function () {
          var watched, action;

          beforeEach(function () {
            // NOTE: This ordering of watches is fragile.
            watched = scope.$watch.calls.argsFor(1)[0]();
            action = scope.$watch.calls.argsFor(1)[1];
          });

          it("watches model.newInstanceSpec.instance_count", function () {
            // value as injected above.
            expect(watched).toEqual(1);
          });

          it("sets the control instanceCount when 1 or more", function () {
            var myScope = {selectFlavorCtrl: ctrl};
            action(5, 3, myScope);
            expect(ctrl.instanceCount).toBe(5);
          });

          it("sets the control instanceCount to 1 when less than 1", function () {
            var myScope = {selectFlavorCtrl: ctrl};
            action(0, 3, myScope);
            expect(ctrl.instanceCount).toBe(1);
          });

          it("does nothing when new value is not defined", function () {
            var myScope = {selectFlavorCtrl: ctrl};
            spyOn(ctrl, 'updateFlavorFacades');
            spyOn(ctrl, 'validateFlavor');
            action(undefined, 3, myScope);
            expect(ctrl.instanceCount).toBe(1);
            expect(ctrl.updateFlavorFacades).not.toHaveBeenCalled();
            expect(ctrl.validateFlavor).not.toHaveBeenCalled();
          });

          it("calls updateFlavorFacades()", function () {
            var myScope = {selectFlavorCtrl: ctrl};
            spyOn(ctrl, 'updateFlavorFacades');
            action('na', 'na', myScope);
            expect(ctrl.updateFlavorFacades).toHaveBeenCalledWith();
          });

          it("calls validateFlavor()", function () {
            var myScope = {selectFlavorCtrl: ctrl};
            spyOn(ctrl, 'validateFlavor');
            action('na', 'na', myScope);
            expect(ctrl.validateFlavor).toHaveBeenCalledWith();
          });
        });
      });

      describe("watch collections", function () {

        it("establishes three watch collections", function () {
          expect(scope.$watchCollection.calls.count()).toBe(3);
        });

        describe("model.flavors", function () {
          var watched, action;

          beforeEach(function () {
            watched = scope.$watchCollection.calls.argsFor(0)[0];
            action = scope.$watchCollection.calls.argsFor(0)[1];
          });

          it("watches model.flavors", function () {
            expect(watched).toBe("model.flavors");
          });

          it("sets the control flavors", function () {
            var myScope = {selectFlavorCtrl: ctrl};
            action('new', 'na', myScope);
            expect(ctrl.flavors).toBe("new");
          });

          it("calls updateFlavorFacades", function () {
            var myScope = {selectFlavorCtrl: ctrl};
            spyOn(ctrl, 'updateFlavorFacades');
            action('na', 'na', myScope);
            expect(ctrl.updateFlavorFacades).toHaveBeenCalledWith();
          });
        });

        describe("selectFlavorCtrl.allocatedFlavorFacades", function () {
          var watched, action;

          beforeEach(function () {
            watched = scope.$watchCollection.calls.argsFor(1)[0];
            action = scope.$watchCollection.calls.argsFor(1)[1];
          });

          it("watches model.flavors", function () {
            expect(watched).toBe("selectFlavorCtrl.allocatedFlavorFacades");
          });

          it("deletes flavor if falsy facade", function () {
            var myScope = {selectFlavorCtrl: ctrl};
            action(false, 'na', myScope);
            expect(model.newInstanceSpec.flavor).not.toBeDefined();
          });

          it("deletes flavor if empty facade", function () {
            var myScope = {selectFlavorCtrl: ctrl};
            action([], 'na', myScope);
            expect(model.newInstanceSpec.flavor).not.toBeDefined();
          });

          it("sets the model's flavor", function () {
            var myScope = {selectFlavorCtrl: ctrl};
            action([{flavor: "raspberry"}], 'na', myScope);
            expect(model.newInstanceSpec.flavor).toEqual("raspberry");
          });

          it("calls validateFlavor", function () {
            var myScope = {selectFlavorCtrl: ctrl};
            spyOn(myScope.selectFlavorCtrl, 'validateFlavor');
            action("na", 'na', myScope);
            expect(myScope.selectFlavorCtrl.validateFlavor).toHaveBeenCalledWith();
          });
        });

        describe("instance spec source changes", function () {
          var watched, action;

          beforeEach(function () {
            watched = scope.$watchCollection.calls.argsFor(2)[0];
            action = scope.$watchCollection.calls.argsFor(2)[1];
          });

          it("watches new instance source", function () {
            expect(watched()).toBe("source_value");
          });

          it("sets the source", function () {
            var myScope = {selectFlavorCtrl: ctrl};
            action(['new'], 'na', myScope);
            expect(ctrl.source).toBe("new");
          });

          it("sets the source to null if not provided", function () {
            var myScope = {selectFlavorCtrl: ctrl};
            action(undefined, 'na', myScope);
            expect(ctrl.source).toBeNull();
          });

          it("sets the source to null if not an array", function () {
            var myScope = {selectFlavorCtrl: ctrl};
            action(5, 'na', myScope);
            expect(ctrl.source).toBeNull();
          });

          it("calls updateFlavorFacades", function () {
            var myScope = {selectFlavorCtrl: ctrl};
            spyOn(ctrl, 'updateFlavorFacades');
            action('na', 'na', myScope);
            expect(ctrl.updateFlavorFacades).toHaveBeenCalledWith();
          });

          it("calls validateFlavor", function () {
            var myScope = {selectFlavorCtrl: ctrl};
            spyOn(ctrl, 'validateFlavor');
            action('na', 'na', myScope);
            expect(ctrl.validateFlavor).toHaveBeenCalledWith();
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
            expect(ctrl.defaultIfUndefined(undefined, 'defValue')).toBe('defValue');
          });

          it('returns the value if defined', function () {
            expect(ctrl.defaultIfUndefined('myVal', 'defValue')).toBe('myVal');
          });
        });
      });

    });

    describe('LaunchInstanceFlavorHelpCtrl', function () {
      var ctrl;

      beforeEach(module('hz.dashboard.launch-instance'));

      beforeEach(inject(function ($controller) {
        ctrl = $controller('LaunchInstanceFlavorHelpCtrl', {});
      }));

      it('defines the title', function () {
        expect(ctrl.title).toBeDefined();
      });

      it('defines paragraphs', function () {
        expect(ctrl.paragraphs).toBeDefined();
        expect(ctrl.paragraphs.length).toBeGreaterThan(0);
      });

    });

  });

})();
