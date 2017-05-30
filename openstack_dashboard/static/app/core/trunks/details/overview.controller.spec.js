/*
 * Copyright 2017 Ericsson
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

  describe('trunk overview controller', function() {
    var ctrl;
    var sessionObj = {project_id: '12'};
    var neutron = {
      getNamespaces: angular.noop
    };

    beforeEach(module('horizon.app.core.trunks'));
    beforeEach(module('horizon.framework.conf'));
    beforeEach(inject(function($controller, $q, $injector) {
      var session = $injector.get('horizon.app.core.openstack-service-api.userSession');
      var deferred = $q.defer();
      var sessionDeferred = $q.defer();
      deferred.resolve({data: {sub_ports: [{'port_id': '1', 'seg_id': 2}, [], {}]}});
      sessionDeferred.resolve(sessionObj);
      spyOn(neutron, 'getNamespaces').and.returnValue(deferred.promise);
      spyOn(session, 'get').and.returnValue(sessionDeferred.promise);
      ctrl = $controller('TrunkOverviewController',
        {
          '$scope': {context: {loadPromise: deferred.promise}}
        }
      );
    }));

    it('sets ctrl.resourceType', function() {
      expect(ctrl.resourceType).toBeDefined();
    });

    it('sets ctrl.trunk.sub_ports', inject(function($timeout) {
      $timeout.flush();
      expect(ctrl.trunk).toBeDefined();
      expect(ctrl.trunk.sub_ports).toBeDefined();
      expect(ctrl.trunk.sub_ports[0]).toEqual({'port_id': '1', 'seg_id': 2});
    }));

    it('sets ctrl.trunk.sub_ports if empty array', inject(function($timeout) {
      $timeout.flush();
      expect(ctrl.trunk).toBeDefined();
      expect(ctrl.trunk.sub_ports).toBeDefined();
      expect(ctrl.trunk.sub_ports[1]).toEqual([]);
    }));

    it('sets ctrl.trunk.sub_ports if empty object', inject(function($timeout) {
      $timeout.flush();
      expect(ctrl.trunk).toBeDefined();
      expect(ctrl.trunk.sub_ports).toBeDefined();
      expect(ctrl.trunk.sub_ports[2]).toEqual({});
    }));

    it('sets ctrl.projectId', inject(function($timeout) {
      $timeout.flush();
      expect(ctrl.projectId).toBe(sessionObj.project_id);
    }));

  });

})();
