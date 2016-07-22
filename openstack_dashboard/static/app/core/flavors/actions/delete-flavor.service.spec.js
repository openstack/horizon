/*
 * (c) Copyright 2016 Hewlett Packard Enterprise Development LP
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use self file except in compliance with the License. You may obtain
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

(function() {
  'use strict';

  describe('horizon.app.core.flavors.actions.delete-flavor.service', function() {

    var service, deleteModalService, novaAPI;

    ///////////////////////

    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.flavors'));
    beforeEach(module('horizon.framework'));

    beforeEach(inject(function($injector) {
      service = $injector.get('horizon.app.core.flavors.actions.delete-flavor.service');
      novaAPI = $injector.get('horizon.app.core.openstack-service-api.nova');
      deleteModalService = $injector.get('horizon.framework.widgets.modal.deleteModalService');
    }));

    describe('perform method', function() {

      beforeEach(function() {
        spyOn(deleteModalService, 'open').and.returnValue({then: angular.noop});
      });

      ////////////

      it('should open the delete modal and show correct labels, single object', testSingleLabels);
      it('should open the delete modal and show correct labels, plural objects', testPluralLabels);
      it('should open the delete modal with correct entities', testEntities);
      it('should only delete flavors that are valid', testValids);
      it('should pass in a function that deletes an flavor', testNova);

      ////////////

      function testSingleLabels() {
        var flavors = {name: 'puffy'};
        service.perform(flavors);

        var labels = deleteModalService.open.calls.argsFor(0)[2].labels;
        expect(deleteModalService.open).toHaveBeenCalled();
        angular.forEach(labels, function eachLabel(label) {
          expect(label.toLowerCase()).toContain('flavor');
        });
      }

      function testPluralLabels() {
        var flavors = [{name: 'puffy'}, {name: 'puffin'}];
        service.perform(flavors);

        var labels = deleteModalService.open.calls.argsFor(0)[2].labels;
        expect(deleteModalService.open).toHaveBeenCalled();
        angular.forEach(labels, function eachLabel(label) {
          expect(label.toLowerCase()).toContain('flavors');
        });
      }

      function testEntities() {
        var flavors = [{name: 'puff'}, {name: 'puffy'}, {name: 'puffin'}];
        service.perform(flavors);

        var entities = deleteModalService.open.calls.argsFor(0)[1];
        expect(deleteModalService.open).toHaveBeenCalled();
        expect(entities.length).toEqual(flavors.length);
      }

      function testValids() {
        var flavors = [{name: 'puff'}, {name: 'puffy'}, {name: 'puffin'}];
        service.perform(flavors);

        var entities = deleteModalService.open.calls.argsFor(0)[1];
        expect(deleteModalService.open).toHaveBeenCalled();
        expect(entities.length).toBe(flavors.length);
        expect(entities[0].name).toEqual('puff');
        expect(entities[1].name).toEqual('puffy');
        expect(entities[2].name).toEqual('puffin');
      }

      function testNova() {
        spyOn(novaAPI, 'deleteFlavor').and.callFake(angular.noop);
        var flavors = [{id: 7, name: 'puff'}, {id: 14, name: 'cake'}];
        service.perform(flavors);

        var contextArg = deleteModalService.open.calls.argsFor(0)[2];
        var deleteFunction = contextArg.deleteEntity;
        deleteFunction(flavors[0].id);
        expect(novaAPI.deleteFlavor).toHaveBeenCalledWith(flavors[0].id, true);
      }

    }); // end of delete modal

  }); // end of delete-flavor

})();
