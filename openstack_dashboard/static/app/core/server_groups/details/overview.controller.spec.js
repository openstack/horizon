/*
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

(function() {
  'use strict';

  describe('server group overview controller', function() {
    var $controller, $q, $timeout, nova, session;
    var sessionObj = {project_id: '10'};

    beforeEach(module('horizon.app.core.server_groups'));
    beforeEach(module('horizon.framework.conf'));
    beforeEach(inject(function($injector) {
      $controller = $injector.get('$controller');
      $q = $injector.get('$q');
      $timeout = $injector.get('$timeout');
      session = $injector.get('horizon.app.core.openstack-service-api.userSession');
      nova = $injector.get('horizon.app.core.openstack-service-api.nova');
    }));

    it('sets ctrl.members when server group members length === 0', inject(function() {
      var deferred = $q.defer();
      var serverGroupDeferred = $q.defer();
      var serversDeferred = $q.defer();
      var sessionDeferred = $q.defer();
      deferred.resolve({data: { data: true}});
      serverGroupDeferred.resolve({data: {members: ['1', '2']}});
      serversDeferred.resolve({data: { items: [{'id': '1'}, {'id': '2'}]}});
      sessionDeferred.resolve(sessionObj);
      spyOn(nova, 'isFeatureSupported').and.returnValue(deferred.promise);
      spyOn(nova, 'getServerGroup').and.returnValue(serverGroupDeferred.promise);
      spyOn(nova, 'getServers').and.returnValue(serversDeferred.promise);
      spyOn(session, 'get').and.returnValue(sessionDeferred.promise);
      var ctrl = $controller('ServerGroupOverviewController',
        {
          '$scope': {context: {loadPromise: serverGroupDeferred.promise}}
        }
      );
      $timeout.flush();
      expect(ctrl.properties).toBeDefined();
      expect(ctrl.members[0]).toEqual({'id': '1'});
      expect(ctrl.projectId).toBe(sessionObj.project_id);
    }));

    it('sets ctrl.members when server group members length > 0', inject(function() {
      var deferred = $q.defer();
      var serverGroupDeferred = $q.defer();
      var serversDeferred = $q.defer();
      var sessionDeferred = $q.defer();
      deferred.resolve({data: { data: true}});
      serverGroupDeferred.resolve({data: {members: []}});
      serversDeferred.resolve({data: { items: [{'id': '1'}, {'id': '2'}]}});
      sessionDeferred.resolve(sessionObj);
      spyOn(nova, 'isFeatureSupported').and.returnValue(deferred.promise);
      spyOn(nova, 'getServerGroup').and.returnValue(serverGroupDeferred.promise);
      spyOn(nova, 'getServers').and.returnValue(serversDeferred.promise);
      spyOn(session, 'get').and.returnValue(sessionDeferred.promise);
      var ctrl = $controller('ServerGroupOverviewController',
        {
          '$scope': {context: {loadPromise: serverGroupDeferred.promise}}
        }
      );
      $timeout.flush();
      expect(ctrl.properties).toBeDefined();
      expect(ctrl.members).toEqual([]);
      expect(ctrl.projectId).toBe(sessionObj.project_id);
    }));
  });
})();
