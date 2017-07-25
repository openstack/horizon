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

  describe('network qos overview controller', function() {
    var ctrl;
    var sessionObj = {project_id: '12'};
    var neutron = {
      getNamespaces: angular.noop
    };

    beforeEach(module('horizon.app.core.network_qos'));
    beforeEach(module('horizon.framework.conf'));
    beforeEach(inject(function($controller, $q, $injector) {
      var session = $injector.get('horizon.app.core.openstack-service-api.userSession');
      var deferred = $q.defer();
      var sessionDeferred = $q.defer();
      deferred.resolve({data: {rules: [{'a': 'apple'}, [], {}]}});
      sessionDeferred.resolve(sessionObj);
      spyOn(neutron, 'getNamespaces').and.returnValue(deferred.promise);
      spyOn(session, 'get').and.returnValue(sessionDeferred.promise);
      ctrl = $controller('NetworkQoSOverviewController',
        {
          '$scope': {context: {loadPromise: deferred.promise}}
        }
      );
    }));

    it('sets ctrl.resourceType', function() {
      expect(ctrl.resourceType).toBeDefined();
    });

    it('sets ctrl.policy.rules (metadata)', inject(function($timeout) {
      $timeout.flush();
      expect(ctrl.policy).toBeDefined();
      expect(ctrl.policy.rules).toBeDefined();
      expect(ctrl.policy.rules[0]).toEqual({'a': 'apple'});
    }));

    it('sets ctrl.policy.rules propValue if empty array', inject(function($timeout) {
      $timeout.flush();
      expect(ctrl.policy).toBeDefined();
      expect(ctrl.policy.rules).toBeDefined();
      expect(ctrl.policy.rules[1]).toEqual([]);
    }));

    it('sets ctrl.policy.rules propValue if empty object', inject(function($timeout) {
      $timeout.flush();
      expect(ctrl.policy).toBeDefined();
      expect(ctrl.policy.rules).toBeDefined();
      expect(ctrl.policy.rules[2]).toEqual({});
    }));

    it('sets ctrl.projectId', inject(function($timeout) {
      $timeout.flush();
      expect(ctrl.projectId).toBe(sessionObj.project_id);
    }));

  });

})();
