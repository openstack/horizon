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
    var $controller, treeService, modalInstance;

    var metadataService = {
      editMetadata: function() {}
    };

    beforeEach(function() {
      modalInstance = {
        dismiss: jasmine.createSpy(),
        close: jasmine.createSpy()
      };
    });

    beforeEach(module('horizon.app.core.metadata.modal',
      'horizon.framework.widgets.metadata.tree'));
    beforeEach(inject(function (_$controller_, $injector) {
      $controller = _$controller_;
      treeService = $injector.get('horizon.framework.widgets.metadata.tree.service');
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
          then: function(success, fail) {
            success();
          }
        };
      };

      spyOn(metadataService, 'editMetadata').and.callThrough();

      controller.save();

      expect(modalInstance.close).toHaveBeenCalled();
      expect(metadataService.editMetadata)
        .toHaveBeenCalledWith('aggregate', '123', {someProperty: 'someValue'}, []);
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
        .toHaveBeenCalledWith('aggregate', '123', {someProperty: 'someValue'}, []);
    });

    function createController() {
      return $controller('MetadataModalController', {
        '$modalInstance': modalInstance,
        'horizon.framework.widgets.metadata.tree.service': treeService,
        'horizon.app.core.metadata.service': metadataService,
        'available': {data: {}},
        'existing': {data: {someProperty: 'someValue'}},
        'params': {resource: 'aggregate', id: '123'}
      });
    }
  });
})();
