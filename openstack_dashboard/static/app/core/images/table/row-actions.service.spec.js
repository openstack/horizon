/**
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

(function() {
  'use strict';

  describe('horizon.app.core.images.table.row-actions.service', function() {
    var service;
    var deleteService = {
      initScope: angular.noop
    };
    var createVolumeService = {
      initScope: angular.noop
    };
    var launchInstanceService = {
      initScope: angular.noop
    };
    var updateMetadataService = {
      initScope: angular.noop
    };

    ///////////////////////

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.images', function($provide) {
      $provide.value('horizon.app.core.images.actions.create-volume.service', createVolumeService);
      $provide.value('horizon.app.core.images.actions.row-delete.service', deleteService);
      $provide.value('horizon.app.core.images.actions.launch-instance.service',
                     launchInstanceService);
      $provide.value('horizon.app.core.images.actions.update-metadata.service',
                     updateMetadataService);
    }));

    beforeEach(inject(function ($injector) {
      service = $injector.get('horizon.app.core.images.table.row-actions.service');
    }));

    it('should call initScope on services', function() {
      spyOn(deleteService, 'initScope');
      spyOn(createVolumeService, 'initScope');
      spyOn(launchInstanceService, 'initScope');
      spyOn(updateMetadataService, 'initScope');

      var scope = {$new: function() { return 'custom_scope'; }};
      service.initScope(scope);

      expect(deleteService.initScope).toHaveBeenCalledWith('custom_scope');
      expect(createVolumeService.initScope).toHaveBeenCalledWith('custom_scope');
      expect(launchInstanceService.initScope).not.toHaveBeenCalled();
      expect(updateMetadataService.initScope).toHaveBeenCalledWith('custom_scope');
    });

    it('should return delete action', function() {
      var actions = service.actions();

      expect(actions.length).toEqual(5);
      expect(actions[3].service).toEqual(deleteService);
    });

    it('should return launchInstance action twice', function() {
      var actions = service.actions();

      expect(actions.length).toEqual(5);
      expect(actions[0].service).toEqual(launchInstanceService);
      expect(actions[1].service).toEqual(launchInstanceService);
    });

    it('should return updateMetadata action', function() {
      var actions = service.actions();

      expect(actions.length).toEqual(5);
      expect(actions[2].service).toEqual(updateMetadataService);
    });

    it('should return create volumne action', function() {
      var actions = service.actions();

      expect(actions.length).toEqual(5);
      expect(actions[1].service).toEqual(createVolumeService);
    });

  });
})();
