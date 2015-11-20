/**
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

  describe('horizon.dashboard.admin.flavors.controller.FlavorsTableController', function () {

    var flavors = [{id: '1'}, {id: '2'}];

    var novaAPI = {
      getFlavors: function() {
        var deferred = $q.defer();
        deferred.resolve({data: {items: flavors}});
        return deferred.promise;
      }
    };

    var controller, $q, $scope;

    beforeEach(module('horizon.framework'));

    beforeEach(module('horizon.app.core.openstack-service-api', function($provide) {
      $provide.value('horizon.app.core.openstack-service-api.nova', novaAPI);
    }));

    beforeEach(module('horizon.dashboard.admin', function($provide) {
      $provide.constant('horizon.dashboard.admin.basePath', '/a/sample/path/');
    }));

    beforeEach(module('horizon.dashboard.admin.flavors'));

    beforeEach(inject(function ($injector, _$rootScope_) {
      $scope = _$rootScope_.$new();
      $q = $injector.get('$q');
      controller = $injector.get('$controller');
    }));

    function createController() {
      return controller('FlavorsTableController', {});
    }

    it('should invoke nova apis', function() {
      spyOn(novaAPI, 'getFlavors').and.callThrough();

      var ctrl = createController();
      $scope.$apply();

      expect(novaAPI.getFlavors).toHaveBeenCalled();
      expect(ctrl.flavors).toEqual(flavors);
      expect(ctrl.iflavors).toBeDefined();
    });

  });

})();
