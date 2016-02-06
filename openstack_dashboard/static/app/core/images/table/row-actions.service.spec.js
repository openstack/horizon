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

  describe('horizon.app.core.images.row-actions.service', function() {
    var service;
    var deleteService = {
      initScope: angular.noop
    };
    var createVolumeService = {
      initScope: angular.noop
    };

    ///////////////////////

    beforeEach(module('horizon.framework'));

    beforeEach(module('horizon.app.core.images', function($provide) {
      $provide.value('horizon.app.core.images.actions.deleteService', deleteService);
      $provide.value('horizon.app.core.images.actions.createVolumeService', createVolumeService);
    }));

    beforeEach(inject(function ($injector) {
      service = $injector.get('horizon.app.core.images.row-actions.service');
    }));

    it('should call initScope on services', function() {
      spyOn(deleteService, 'initScope');
      spyOn(createVolumeService, 'initScope');

      var scope = {$new: function() { return 'custom_scope'; }};
      service.initScope(scope);

      expect(deleteService.initScope).toHaveBeenCalledWith('custom_scope');
      expect(createVolumeService.initScope).toHaveBeenCalledWith('custom_scope');
    });

    it('should return delete action', function() {
      var actions = service.actions();

      expect(actions.length).toEqual(2);
      expect(actions[0].service).toEqual(deleteService);
    });

    it('should return create volumne action', function() {
      var actions = service.actions();

      expect(actions.length).toEqual(2);
      expect(actions[1].service).toEqual(createVolumeService);
    });

  });
})();
