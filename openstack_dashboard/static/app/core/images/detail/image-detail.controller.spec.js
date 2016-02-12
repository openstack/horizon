/*
 *
 * Licensed under the Apache License, Version 2.0 (the 'License');
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an 'AS IS' BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function() {
  'use strict';

  describe('horizon.app.core.images', function() {

    beforeEach(module('ui.bootstrap'));
    beforeEach(module('horizon.app.core'));

    describe("ImageDetailController", function() {
      var ctrl, glanceAPI, keystoneAPI, imageMock, projectMock, tableRoute;

      beforeEach(inject(function($injector, $controller) {
        imageMock = {
          owner: 'mock_image_owner',
          properties: {
            kernel_id: 'mock_kernel_id'
          }
        };

        projectMock = {
          name: 'mock_project'
        };

        keystoneAPI = {
          getProject: function() {
            return {
              success: function(callback) {
                callback(projectMock);
              }
            };
          }
        };

        glanceAPI = {
          getImage: function() {
            return {
              success: function(callback) {
                callback(imageMock);
              }
            };
          }
        };

        spyOn(glanceAPI, 'getImage').and.callThrough();
        spyOn(keystoneAPI, 'getProject').and.callThrough();

        tableRoute = $injector.get('horizon.app.core.images.tableRoute');

        ctrl = $controller("ImageDetailController", {
          'horizon.app.core.openstack-service-api.glance': glanceAPI,
          'horizon.app.core.openstack-service-api.keystone': keystoneAPI,
          '$routeParams': {
            imageId: '1234'
          }
        });
      }));

      it('defines the controller', function() {
        expect(ctrl).toBeDefined();
      });

      it('should set table route', function() {
        expect(ctrl.tableRoute).toEqual(tableRoute);
      });

      it('should create a map of the image properties', function() {
        expect(ctrl.hasCustomProperties).toEqual(true);
        expect(ctrl.image.properties).toEqual([{name: 'kernel_id', value: 'mock_kernel_id'}]);
      });
    });

  });

})();
