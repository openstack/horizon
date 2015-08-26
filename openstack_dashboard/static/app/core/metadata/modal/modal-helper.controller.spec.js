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

  describe('MetadataModalHelperController', function () {
    var $controller, $window;

    var metadataModalService = {
      open: function () {
        return {
          result: {
            then: function (callback) {
              callback();
            }
          }
        };
      }
    };

    beforeEach(function() {
      $window = {
        location: {
          reload: jasmine.createSpy()
        }
      };
    });

    beforeEach(module('horizon.app.core.metadata.modal'));
    beforeEach(inject(function (_$controller_) {
      $controller = _$controller_;
    }));

    it('should reload window if required', function () {
      var params = {
        $window: $window,
        'horizon.app.core.metadata.modal.service': metadataModalService
      };
      var controller = $controller('MetadataModalHelperController', params);
      controller.openMetadataModal('aggregate', '123', true);
      expect($window.location.reload).toHaveBeenCalled();
    });

    it('should not reload window if not required', function () {
      var params = {
        $window: $window,
        'horizon.app.core.metadata.modal.service': metadataModalService
      };
      var controller = $controller('MetadataModalHelperController', params);
      controller.openMetadataModal('aggregate', '123', false);
      expect($window.location.reload).not.toHaveBeenCalled();
    });

  });
})();
