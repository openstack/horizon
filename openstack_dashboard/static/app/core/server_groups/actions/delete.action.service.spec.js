/*
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

  describe('horizon.app.core.server_groups.actions.delete.service', function() {

    var $scope, deferredModal, novaAPI, service, $location;
    var deleteModalService = {
      open: function () {
        deferredModal.resolve({
          pass: [{context: {id: 'pass'}}],
          fail: [{context: {id: 'fail'}}]
        });
        return deferredModal.promise;
      }
    };

    ///////////////////////

    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.server_groups'));
    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.framework.widgets.modal', function($provide) {
      $provide.value('horizon.framework.widgets.modal.deleteModalService', deleteModalService);
    }));
    beforeEach(inject(function($injector, _$rootScope_, $q) {
      $scope = _$rootScope_.$new();
      deferredModal = $q.defer();
      $location = $injector.get("$location");
      novaAPI = $injector.get('horizon.app.core.openstack-service-api.nova');
      service = $injector.get('horizon.app.core.server_groups.actions.delete.service');
    }));

    describe('perform method', function() {

      beforeEach(function() {
        spyOn(deleteModalService, 'open').and.callThrough();
      });

      ////////////

      it('should open the delete modal and show correct labels, single object', testSingleLabels);
      it('should open the delete modal and show correct labels, plural objects', testPluralLabels);
      it('should open the delete modal with correct entities', testEntities);
      it('should only delete server groups that are valid', testValids);
      it('should pass in a function that deletes a server group', testNova);
      it('should check the policy if the user is allowed to delete server group', testAllowed);
      it('Should jump to the project server_groups page when deleting the server_groups',
         testDeleteResult);

      ////////////

      function testSingleLabels() {
        var servergroups = {name: 'sg'};
        service.perform(servergroups);

        $scope.$apply();

        var labels = deleteModalService.open.calls.argsFor(0)[2].labels;
        expect(deleteModalService.open).toHaveBeenCalled();
        angular.forEach(labels, function eachLabel(label) {
          expect(label.toLowerCase()).toContain('server group');
        });
      }

      function testPluralLabels() {
        var servergroups = [{name: 'sg1'}, {name: 'sg2'}];
        service.perform(servergroups);

        $scope.$apply();

        var labels = deleteModalService.open.calls.argsFor(0)[2].labels;
        expect(deleteModalService.open).toHaveBeenCalled();
        angular.forEach(labels, function eachLabel(label) {
          expect(label.toLowerCase()).toContain('server groups');
        });
      }

      function testEntities() {
        var servergroups = [{name: 'sg1'}, {name: 'sg2'}, {name: 'sg3'}];
        service.perform(servergroups);

        $scope.$apply();

        var entities = deleteModalService.open.calls.argsFor(0)[1];
        expect(deleteModalService.open).toHaveBeenCalled();
        expect(entities.length).toEqual(servergroups.length);
      }

      function testValids() {
        var servergroups = [{name: 'sg1'}, {name: 'sg2'}, {name: 'sg3'}];
        service.perform(servergroups);

        $scope.$apply();

        var entities = deleteModalService.open.calls.argsFor(0)[1];
        expect(deleteModalService.open).toHaveBeenCalled();
        expect(entities.length).toBe(servergroups.length);
        expect(entities[0].name).toEqual('sg1');
        expect(entities[1].name).toEqual('sg2');
        expect(entities[2].name).toEqual('sg3');
      }

      function testNova() {
        spyOn(novaAPI, 'deleteServerGroup').and.callFake(angular.noop);
        var servergroups = [{id: 1, name: 'sg1'}, {id: 2, name: 'sg2'}];
        service.perform(servergroups);

        $scope.$apply();

        var contextArg = deleteModalService.open.calls.argsFor(0)[2];
        var deleteFunction = contextArg.deleteEntity;
        deleteFunction(servergroups[0].id);
        expect(novaAPI.deleteServerGroup).toHaveBeenCalledWith(servergroups[0].id, true);
      }

      function testAllowed() {
        var allowed = service.allowed();
        expect(allowed).toBeTruthy();
      }

      function testDeleteResult() {
        $location.path("ngdetails/OS::Nova::ServerGroup/1");
        var servergroup = {id: 1, name: 'sg1'};
        deferredModal.resolve({fail: [], pass:[{data:{"data": "", "status": "204"},
                                                context:servergroup}]});
        spyOn(novaAPI, 'deleteServerGroup').and.returnValue(deferredModal.promise);
        service.perform(servergroup);
        $scope.$apply();

        var contextArg = deleteModalService.open.calls.argsFor(0)[2];
        var deleteFunction = contextArg.deleteEntity;
        deleteFunction(servergroup.id);
        expect(novaAPI.deleteServerGroup).toHaveBeenCalledWith(servergroup.id, true);
        expect($location.path()).toEqual("/project/server_groups");
      }

    }); // end of delete modal

  }); // end of delete server group

})();
