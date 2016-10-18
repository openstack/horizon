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

  describe('Identity domains details module', function() {
    it('should exist', function() {
      expect(angular.module('horizon.dashboard.identity.domains.details')).toBeDefined();
    });
  });

  describe('domain overview controller', function() {
    var ctrl, $scope;

    beforeEach(module('horizon.dashboard.identity.domains'));
    beforeEach(module('horizon.framework.conf'));
    beforeEach(inject(function($controller, $injector, $q, _$rootScope_) {
      var deferred = $q.defer();
      deferred.resolve({data: {id: '1234', 'name': 'test'}});
      ctrl = $controller('DomainOverviewController',
        {'$scope': {context: {loadPromise: deferred.promise}}}
      );
      $scope = _$rootScope_.$new();
    }));

    it('sets ctrl.resourceType', function() {
      expect(ctrl.resourceType).toBeDefined();
    });

    it('sets ctrl.domain', inject(function() {
      $scope.$apply();
      expect(ctrl.domain).toBeDefined();
    }));

  });

})();

