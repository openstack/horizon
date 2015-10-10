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

  describe('horizon.app.core.images.actions.deleteService', function() {

    var deleteImageService = {
      initScope: function() {},
      perform: function () {}
    };

    var service, $scope;

    ///////////////////////

    beforeEach(module('horizon.framework.util'));
    beforeEach(module('horizon.framework.util.http'));

    beforeEach(module('horizon.framework.widgets'));
    beforeEach(module('horizon.framework.widgets.toast'));

    beforeEach(module('horizon.app.core'));

    beforeEach(module('horizon.app.core.images', function($provide) {
      $provide.value('horizon.app.core.images.actions.deleteImageService', deleteImageService);
    }));

    beforeEach(inject(function($injector, _$rootScope_) {
      $scope = _$rootScope_.$new();
      service = $injector.get('horizon.app.core.images.actions.deleteService');
    }));

    it('should init the deleteImageService', function() {
      spyOn(deleteImageService, 'initScope').and.callThrough();

      service.initScope($scope);

      expect(deleteImageService.initScope).toHaveBeenCalled();
    });

    it('pass the image to the deleteImageService', function() {
      spyOn(deleteImageService, 'perform').and.callThrough();
      var image = {id: '1', name: 'name', extra: 'extra'};
      service.perform(image);

      expect(deleteImageService.perform).toHaveBeenCalledWith([image]);
    });

  });

})();
