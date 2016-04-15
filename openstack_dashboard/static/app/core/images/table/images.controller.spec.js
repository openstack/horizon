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
      }
    };

    var expectedImages = {
      1: {id: '1', visibility: 'public', filtered_visibility: 'Public'},
      2: {id: '2', is_public: false, owner: 'not_me', filtered_visibility: 'Shared with Me'}
    };

    var $scope, controller, events, detailsRoute;

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
      events = $injector.get('horizon.app.core.images.events');
      controller = $injector.get('$controller');
      detailsRoute = $injector.get('horizon.app.core.images.detailsRoute');

      spyOn(glanceAPI, 'getImages').and.callThrough();
      spyOn(glanceAPI, 'getNamespaces').and.callThrough();
      spyOn(userSession, 'get').and.callThrough();
      spyOn(mockQ, 'all').and.callThrough();

    }));

    function createController() {
      return controller('horizon.app.core.images.table.ImagesController', {
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
      var ctrl = createController();
      expect(userSession.get).toHaveBeenCalled();
      expect(glanceAPI.getImages).toHaveBeenCalled();
      expect(ctrl.imagesSrc).toEqual([
        expectedImages['1'],
        expectedImages['2']
      ]);
      expect(glanceAPI.getNamespaces).toHaveBeenCalled();
    });

    it('should refresh images after delete', function() {
      var ctrl = createController();
      expect(ctrl.imagesSrc).toEqual([
        expectedImages['1'],
        expectedImages['2']
      ]);

      spyOn($scope, '$emit').and.callThrough();
      $scope.$emit(events.DELETE_SUCCESS, ['1']);

      expect(ctrl.imagesSrc).toEqual([
        expectedImages['2']
      ]);

      expect($scope.$emit).toHaveBeenCalledWith('hzTable:clearSelected');
    });

    it('should refresh images after update', function() {
      var ctrl = createController();
      expect(ctrl.imagesSrc).toEqual(images);

      $scope.$emit(events.UPDATE_SUCCESS, {id: '1', name: 'name_new'});

      expect(ctrl.imagesSrc.filter(function (x) { return x.id === '1'; })[0].name).toBe('name_new');
    });

    it('should destroy the event watcher for delete', function() {
      var ctrl = createController();

      $scope.$emit('$destroy');
      $scope.$emit(events.DELETE_SUCCESS, ['1']);

      expect(ctrl.imagesSrc).toEqual([
        expectedImages['1'],
        expectedImages['2']
      ]);
    });

    it('should destroy the event watcher for update', function() {
      var ctrl = createController();

      $scope.$emit('$destroy');
      $scope.$emit(events.UPDATE_SUCCESS, {id: '1', name: 'name_new'});

      expect(ctrl.imagesSrc).toEqual(images);
    });

    it('should destroy the event watcher for create', function() {
      var ctrl = createController();

      $scope.$emit('$destroy');
      $scope.$emit(events.createSuccess, {id: '3'});

      expect(ctrl.imagesSrc).toEqual(images);
    });

  });
})();
