/**
 * Copyright 2015 ThoughtWorks Inc.
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

  describe('MetadataModalController', function () {
    var $controller, treeService, modalInstance, toast;

    var metadataService = {
      editMetadata: function() {}
    };

    var availableItem = {
      'namespace': 'bug1606988',
      'properties': {
        'UPPER_lower': {
          'items': {
            'enum': [
              'foo',
              'bar'
            ],
            'type': 'string'
          },
          'type': 'array'
        }
      }
    };

    var existing = {
      'upper_lower': 'foo',
      'custom': 'bar'
    };

    beforeEach(function() {
      modalInstance = {
        dismiss: jasmine.createSpy(),
        close: jasmine.createSpy()
      };
    });

    beforeEach(module('horizon.app.core.metadata.modal',
      'horizon.framework'));
    beforeEach(inject(function (_$controller_, $injector) {
      $controller = _$controller_;
      treeService = $injector.get('horizon.framework.widgets.metadata.tree.service');
      toast = $injector.get('horizon.framework.widgets.toast.service');
      spyOn(toast, 'add');
    }));

    it('should dismiss modal on cancel', function () {
      var controller = createController(modalInstance);

      controller.cancel();

      expect(modalInstance.dismiss).toHaveBeenCalledWith('cancel');
    });

    it('should close modal on successful save', function () {
      var controller = createController(modalInstance);
      metadataService.editMetadata = function() {
        return {
          then: function(success) {
            success();
          }
        };
      };

      spyOn(metadataService, 'editMetadata').and.callThrough();

      controller.save();

      expect(modalInstance.close).toHaveBeenCalled();
      expect(metadataService.editMetadata)
        .toHaveBeenCalledWith('aggregate', '123', {'custom': 'bar'}, ['UPPER_lower']);
      expect(toast.add).toHaveBeenCalledWith('success', 'Metadata was successfully updated.');
    });

    it('should clear saving flag on failed save', function() {
      var controller = createController(modalInstance);
      metadataService.editMetadata = function() {
        return {
          then: function(success, fail) {
            fail();
          }
        };
      };

      spyOn(metadataService, 'editMetadata').and.callThrough();

      controller.save();

      expect(modalInstance.close).not.toHaveBeenCalled();
      expect(metadataService.editMetadata)
        .toHaveBeenCalledWith('aggregate', '123', {'custom': 'bar'}, ['UPPER_lower']);
      expect(toast.add).toHaveBeenCalledWith('error', 'Unable to update metadata.');
    });

    function createController() {
      //Purposely use different cases in available and existing.
      return $controller('MetadataModalController', {
        '$uibModalInstance': modalInstance,
        'horizon.framework.widgets.metadata.tree.service': treeService,
        'horizon.app.core.metadata.service': metadataService,
        'available': {data: {items: [availableItem]}},
        'existing': {data: existing},
        'params': {resource: 'aggregate', id: '123'}
      });
    }
  });
})();
