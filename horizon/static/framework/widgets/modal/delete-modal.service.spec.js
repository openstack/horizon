/**
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

  describe('horizon.framework.widgets.modal.deleteModalService', function() {
    var labels = {
      title: gettext('Confirm Delete Foobars'),
      message: gettext('selected "%s"'),
      submit: gettext('Delete'),
      success: gettext('Deleted : %s.'),
      error: gettext('Unable to delete: %s.')
    };

    var entityAPI = {
      deleteEntity: function(entityId) {
        var deferred = $q.defer();

        if (entityId === 'bad') {
          deferred.reject();
        } else {
          deferred.resolve();
        }

        return deferred.promise;
      }
    };

    var simpleModalService = {
      modal: function () {
        return {
          result: {
            then: function (callback) {
              callback();
            }
          }
        };
      }
    };

    var toastService = {
      add: function() {}
    };

    var $scope, $q, service, events;

    function getContext() {
      return {
        labels: labels,
        deleteEntity: entityAPI.deleteEntity,
        successEvent: 'custom_delete_event_passed',
        failedEvent: 'custom_delete_event_failed'
      };
    }

    ///////////////////////

    beforeEach(module('horizon.framework.util'));
    beforeEach(module('horizon.framework.widgets'));

    beforeEach(module(function($provide) {
      $provide.value('horizon.framework.widgets.modal.simple-modal.service', simpleModalService);
      $provide.value('horizon.framework.widgets.toast.service', toastService);
    }));

    beforeEach(inject(function($injector, _$rootScope_) {
      $scope = _$rootScope_.$new();
      $q = $injector.get('$q');
      service = $injector.get('horizon.framework.widgets.modal.deleteModalService');
    }));

    it('should open the modal with correct message', function() {
      var fakeModalService = {
        result: {
          then: function (callback) {}
        }
      };

      var entities = [
        {name: 'entity1', id: '1'},
        {id: '2'}
      ];

      spyOn(simpleModalService, 'modal').and.returnValue(fakeModalService);

      service.open($scope, entities, getContext());

      expect(simpleModalService.modal).toHaveBeenCalled();

      var args = simpleModalService.modal.calls.argsFor(0)[0];
      expect(args.body).toEqual('selected "entity1", "2"');
    });

    it('should call entityAPI to delete entities and raise events', function() {
      spyOn(toastService, 'add').and.callThrough();
      spyOn($scope, '$emit').and.callThrough();
      spyOn(entityAPI, 'deleteEntity').and.callThrough();

      var entities = [
        {name: 'entity1', id: '1'},
        {name: 'entity2', id: '2'}
      ];

      service.open($scope, entities, getContext());

      $scope.$apply();

      expect(entityAPI.deleteEntity).toHaveBeenCalledWith('1');
      expect(entityAPI.deleteEntity).toHaveBeenCalledWith('2');
      expect(toastService.add).toHaveBeenCalledWith('success', 'Deleted : entity1, entity2.');
      expect($scope.$emit).toHaveBeenCalledWith('custom_delete_event_passed', [ '1', '2' ]);
    });

    it('should raise failed events if Entity is not deleted', function() {
      spyOn(toastService, 'add').and.callThrough();
      spyOn($scope, '$emit').and.callThrough();
      spyOn(entityAPI, 'deleteEntity').and.callThrough();

      var entities = [{name: 'entity1', id: 'bad'}];

      service.open($scope, entities, getContext());

      $scope.$apply();

      expect(entityAPI.deleteEntity).toHaveBeenCalledWith('bad');
      expect(toastService.add).toHaveBeenCalledWith('error', 'Unable to delete: entity1.');
      expect($scope.$emit).toHaveBeenCalledWith('custom_delete_event_failed', ['bad']);
    });

    it('should raise passed and failed events only for deleted entities', function() {
      spyOn(toastService, 'add').and.callThrough();
      spyOn(entityAPI, 'deleteEntity').and.callThrough();
      spyOn($scope, '$emit').and.callThrough();

      var entities = [
        {name: 'bad_entity', id: 'bad'},
        {name: 'entity2', id: '1'}
      ];

      service.open($scope, entities, getContext());

      $scope.$apply();

      expect(entityAPI.deleteEntity).toHaveBeenCalledWith('bad');
      expect(entityAPI.deleteEntity).toHaveBeenCalledWith('1');
      expect(toastService.add).toHaveBeenCalledWith('success', 'Deleted : entity2.');
      expect(toastService.add).toHaveBeenCalledWith('error', 'Unable to delete: bad_entity.');
      expect($scope.$emit).toHaveBeenCalledWith('custom_delete_event_passed', ['1']);
      expect($scope.$emit).toHaveBeenCalledWith('custom_delete_event_failed', ['bad']);
    });

  });

})();
