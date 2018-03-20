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

  describe('horizon.dashboard.identity.users.actions.workflow.service', function() {

    var $q, $scope, workflow, keystone;

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.dashboard.identity.users'));

    beforeEach(inject(function($injector, _$rootScope_, _$q_) {
      $scope = _$rootScope_.$new();
      $q = _$q_;
      workflow = $injector.get('horizon.dashboard.identity.users.actions.workflow.service');
      keystone = $injector.get('horizon.app.core.openstack-service-api.keystone');
    }));

    function testInitWorkflow(version) {
      var deferredVersion = $q.defer();
      var deferredDefaultDomain = $q.defer();
      var deferredProjects = $q.defer();
      var deferredRoles = $q.defer();
      spyOn(keystone, 'getVersion').and.returnValue(deferredVersion.promise);
      spyOn(keystone, 'getDefaultDomain').and.returnValue(deferredDefaultDomain.promise);
      spyOn(keystone, 'getProjects').and.returnValue(deferredProjects.promise);
      spyOn(keystone, 'getRoles').and.returnValue(deferredRoles.promise);
      deferredVersion.resolve({data: {version: version}});
      deferredDefaultDomain.resolve({data: {items: [{name: 'dom1', id: '12345'}]}});
      deferredProjects.resolve({data: {items: [{name: 'proj1', id: '12345'}]}});
      deferredRoles.resolve({data: {items: [{name: 'role1', id: '12345'}]}});

      var config = workflow.init();
      $scope.$apply();

      expect(config.schema).toBeDefined();
      expect(config.form).toBeDefined();
      expect(config.model).toBeDefined();
      return config;
    }

    it('should create workflow config for creation using Keystone V3', function() {
      var config = testInitWorkflow('3');

      expect(config.form[0].items[1].items[0].condition).not.toBeDefined();
      expect(config.form[0].items[2].items[0].condition).not.toBeDefined();
    });

    it('should create workflow config and the config does not show domain info ' +
       'when use Keystone V2', function() {
      var config = testInitWorkflow('2');

      expect(config.form[0].items[1].items[0].condition).toBe(true);
      expect(config.form[0].items[2].items[0].condition).toBe(true);
    });
  });
})();
