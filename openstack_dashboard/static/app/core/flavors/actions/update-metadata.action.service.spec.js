/**
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

  describe('horizon.app.core.flavors.actions.update-metadata.service', function() {
    var service;

    var metadataModalMock = {
      open: function () {}
    };

    ///////////////////////

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.metadata.modal', function($provide) {
      $provide.value('horizon.app.core.metadata.modal.service', metadataModalMock);
    }));

    beforeEach(inject(function($injector) {
      service = $injector.get('horizon.app.core.flavors.actions.update-metadata.service');
    }));

    it('should open the modal with correct message', function() {
      var fakeModalService = {
        result: {
          then: function (callback) {
            callback();
          }
        }
      };

      spyOn(metadataModalMock, 'open').and.returnValue(fakeModalService);

      service.perform({id: '1', name: 'flavor1'});

      expect(metadataModalMock.open).toHaveBeenCalled();
      expect(metadataModalMock.open.calls.argsFor(0)).toEqual(['flavor', '1']);
    });

  });
})();
