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

  describe('horizon.app.core.network_qos.actions.workflow.service', function() {

    var $q, $scope, workflow, service;

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.network_qos'));

    beforeEach(inject(function($injector, _$rootScope_, _$q_) {
      $scope = _$rootScope_.$new();
      $q = _$q_;
      workflow = $injector.get('horizon.app.core.network_qos.actions.workflow.service');
      service = $injector.get('horizon.app.core.network_qos.actions.create.service');
    }));

    function testInitWorkflow() {
      var deferred = $q.defer();
      spyOn(service, 'perform').and.returnValue(deferred.promise);
      deferred.resolve({'a1': 'n1'});

      var config = workflow.init();
      $scope.$apply();

      expect(config.schema).toBeDefined();
      expect(config.form).toBeDefined();
      expect(config.model).toBeDefined();
      return config;
    }

    it('should create workflow config for creation', function() {
      testInitWorkflow();
    });
  });
})();
