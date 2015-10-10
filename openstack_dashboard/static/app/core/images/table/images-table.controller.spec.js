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

    var glanceAPI = {
      getImages: function() {
        return {
          success: function(callback) {
            callback({items : [{id: '1'},{id: '2'}]});
          }
        };
      }
    };

    var $scope, controller, events;

    beforeEach(module('ui.bootstrap'));
    beforeEach(module('horizon.framework'));

    beforeEach(module('horizon.framework.conf'));
    beforeEach(module('horizon.framework.util.http'));
    beforeEach(module('horizon.framework.widgets.toast'));
    beforeEach(module('horizon.app.core.openstack-service-api', function($provide) {
      $provide.value('horizon.app.core.openstack-service-api.glance', glanceAPI);
    }));

    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.images'));

    beforeEach(inject(function ($injector, _$rootScope_) {
      $scope = _$rootScope_.$new();

      events = $injector.get('horizon.app.core.images.events');
      controller = $injector.get('$controller');

      spyOn(glanceAPI, 'getImages').and.callThrough();
    }));

    function createController() {
      return controller('imagesTableController', {
        glanceAPI: glanceAPI,
        $scope: $scope
      });
    }

    it('should invoke glance apis', function() {
      var ctrl = createController();

      expect(glanceAPI.getImages).toHaveBeenCalled();
      expect(ctrl.imagesSrc).toEqual([{id: '1'}, {id: '2'}]);
    });

    it('should refresh images after delete', function() {
      var ctrl = createController();
      expect(ctrl.imagesSrc).toEqual([{id: '1'}, {id: '2'}]);

      $scope.$emit(events.DELETE_SUCCESS, ['1']);

      expect($scope.selected).toEqual({});
      expect($scope.numSelected).toEqual(0);
      expect(ctrl.imagesSrc).toEqual([{id: '2'}]);
    });

    it('should destroy the event watchers', function() {
      var ctrl = createController();

      $scope.$emit('$destroy');
      $scope.$emit(events.DELETE_SUCCESS, ['1']);

      expect(ctrl.imagesSrc).toEqual([{id: '1'}, {id: '2'}]);
    });

  });
})();
