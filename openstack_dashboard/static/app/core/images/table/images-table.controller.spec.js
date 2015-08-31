/**
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

(function() {
  'use strict';

  describe('horizon.app.core.images table controller', function() {

    function fakeGlance() {
      return {
        success: function(callback) {
          callback({
            items : []
          });
        }
      };
    }

    var controller, glanceAPI, staticUrl;

    ///////////////////////

    beforeEach(module('horizon.framework.conf'));
    beforeEach(module('horizon.framework.util.http'));
    beforeEach(module('horizon.framework.widgets.toast'));
    beforeEach(module('horizon.app.core.openstack-service-api'));

    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.images'));
    beforeEach(inject(function($injector) {

      glanceAPI = $injector.get('horizon.app.core.openstack-service-api.glance');
      controller = $injector.get('$controller');
      staticUrl = $injector.get('$window').STATIC_URL;

      spyOn(glanceAPI, 'getImages').and.callFake(fakeGlance);
    }));

    function createController() {
      return controller('imagesTableController', {
        glanceAPI: glanceAPI
      });
    }

    it('should set path properly', function() {
      var path = staticUrl + 'app/core/images/table/';
      expect(createController().path).toEqual(path);
    });

    it('should invoke glance apis', function() {
      createController();
      expect(glanceAPI.getImages).toHaveBeenCalled();
    });

  });
})();
