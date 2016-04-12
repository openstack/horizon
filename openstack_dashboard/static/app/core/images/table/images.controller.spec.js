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
    var images = [{id: '1', visibility: 'public', filtered_visibility: 'Public'},
              {id: '2', is_public: false, owner: 'not_me', filtered_visibility: 'Shared with Me'}];

    var glanceAPI = {
      getImages: function () {
        return {
          data: {
            items: [
              {id: '1', visibility: 'public', filtered_visibility: 'Public'},
              {id: '2', is_public: false, owner: 'not_me', filtered_visibility: 'Shared with Me'}
            ]
          },
          success: function(callback) {
            callback({items : angular.copy(images)});
          }
        };
      },
      getNamespaces: function () {
        return {
          then: function (callback) {
            callback({data: {items: []}});
          }
        };
      }
    };

    var policy = { allowed: true };
    function fakePolicy() {
      return {
        then: function(successFn, errorFn) {
          if (policy.allowed) { successFn(); }
          else { errorFn(); }
        }
      };
    }
    function fakeToast() { return { add: angular.noop }; }

    var userSession = {
      get: function () {
        return {project_id: '123'};
      }
    };

    var mockQ = {
      all: function (input) {
        return {
          then: function (callback) {
            callback(input);
          }
        };
      },
      when: function (input, callback) {
        return callback(input);
      }
    };

    var expectedImages = {
      1: {id: '1', visibility: 'public', filtered_visibility: 'Public'},
      2: {id: '2', is_public: false, owner: 'not_me', filtered_visibility: 'Shared with Me'}
    };

    var $scope, controller, toastService, detailsRoute, policyAPI;

    beforeEach(module('ui.bootstrap'));
    beforeEach(module('horizon.framework'));

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.openstack-service-api', function($provide) {
      $provide.value('horizon.app.core.openstack-service-api.glance', glanceAPI);
      $provide.value('horizon.app.core.openstack-service-api.userSession', userSession);
    }));

    beforeEach(module('horizon.app.core.images'));

    beforeEach(module('horizon.dashboard.project'));
    beforeEach(module('horizon.dashboard.project.workflow'));
    beforeEach(module('horizon.dashboard.project.workflow.launch-instance'));

    beforeEach(inject(function ($injector, _$rootScope_) {
      $scope = _$rootScope_.$new();

      toastService = $injector.get('horizon.framework.widgets.toast.service');
      policyAPI = $injector.get('horizon.app.core.openstack-service-api.policy');
      controller = $injector.get('$controller');
      detailsRoute = $injector.get('horizon.app.core.images.detailsRoute');

      spyOn(toastService, 'add').and.callFake(fakeToast);
      spyOn(policyAPI, 'ifAllowed').and.callFake(fakePolicy);
      spyOn(glanceAPI, 'getImages').and.callThrough();
      spyOn(glanceAPI, 'getNamespaces').and.callThrough();
      spyOn(userSession, 'get').and.callThrough();
      spyOn(mockQ, 'all').and.callThrough();

    }));

    function createController() {
      return controller('horizon.app.core.images.table.ImagesController', {
        toast: toastService,
        policyAPI: policyAPI,
        glanceAPI: glanceAPI,
        userSession: userSession,
        $q: mockQ,
        $scope: $scope,
        'horizon.app.core.images.row-actions.service': { initScope: angular.noop }
      });
    }

    it('should set details route properly', function() {
      expect(createController().detailsRoute).toEqual(detailsRoute);
    });

    it('should invoke initialization apis', function() {
      policy.allowed = true;
      var ctrl = createController();

      expect(policyAPI.ifAllowed).toHaveBeenCalled();
      expect(glanceAPI.getImages).toHaveBeenCalled();
      expect(userSession.get).toHaveBeenCalled();
      expect(ctrl.imagesSrc).toEqual([
        expectedImages['1'],
        expectedImages['2']
      ]);
      expect(glanceAPI.getNamespaces).toHaveBeenCalled();
    });

    it('re-queries if no result', function() {
      var ctrl = createController();
      glanceAPI.getImages.calls.reset();
      ctrl.actionResultHandler();
      expect(glanceAPI.getImages).toHaveBeenCalled();
    });

    it('re-queries if updated', function() {
      var ctrl = createController();
      glanceAPI.getImages.calls.reset();
      ctrl.actionResultHandler({updated: [{type: 'OS::Glance::Image', id: 'b'}]});
      expect(glanceAPI.getImages).toHaveBeenCalled();
    });

    it('re-queries if created', function() {
      var ctrl = createController();
      glanceAPI.getImages.calls.reset();
      ctrl.actionResultHandler({created: [{type: 'OS::Glance::Image', id: 'b'}]});
      expect(glanceAPI.getImages).toHaveBeenCalled();
    });

    it('does not re-query if only failed', function() {
      var ctrl = createController();
      glanceAPI.getImages.calls.reset();
      ctrl.actionResultHandler({failed: [{type: 'OS::Glance::Image', id: 'b'}]});
      expect(glanceAPI.getImages).not.toHaveBeenCalled();
    });

    it('should remove deleted images', function() {
      var ctrl = createController();
      expect(ctrl.imagesSrc).toEqual([
        expectedImages['1'],
        expectedImages['2']
      ]);

      var result = {
        deleted: [ {type: "OS::Glance::Image", id: '1'} ]
      };
      ctrl.actionResultHandler(result);

      expect(ctrl.imagesSrc).toEqual([
        expectedImages['2']
      ]);
    });

    it('should not remove deleted volumes', function() {
      var ctrl = createController();
      expect(ctrl.imagesSrc).toEqual([
        expectedImages['1'],
        expectedImages['2']
      ]);

      var result = {
        deleted: [ {type: "OS::Cinder::Values", id: '1'} ]
      };
      ctrl.actionResultHandler(result);

      expect(ctrl.imagesSrc).toEqual([
        expectedImages['1'],
        expectedImages['2']
      ]);
    });

    it('should not invoke glance apis if policy fails', function() {
      policy.allowed = false;
      createController();

      expect(policyAPI.ifAllowed).toHaveBeenCalled();
      expect(toastService.add).toHaveBeenCalled();
      expect(glanceAPI.getImages).not.toHaveBeenCalled();
    });

  });
})();
