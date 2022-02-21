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

  describe('horizon.app.core.network_qos.actions.deleteRuleWorkflow.service', function() {

    var $q, $scope, workflow, policies, neutronAPI;

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.network_qos'));

    beforeEach(inject(function($injector, _$rootScope_, _$q_) {
      $q = _$q_;
      $scope = _$rootScope_.$new();
      neutronAPI = $injector.get('horizon.app.core.openstack-service-api.neutron');
      workflow = $injector.get('horizon.app.core.network_qos.actions.deleteRuleWorkflow');
      policies = {
        "data": {
          "created_at": "Z",
          "description": "",
          "id": "1",
          "is_default": false,
          "name": "qos_test",
          "project_id": "5",
          "revision_number": 1,
          "rules": [
            {
              "direction": "egress",
              "id": "1",
              "max_burst_kbps": 1100,
              "max_kbps": 1000,
              "qos_policy_id": "2",
              "type": "bandwidth_limit"
            },
            {
              "dscp_mark": 0,
              "id": "3",
              "qos_policy_id": "2",
              "type": "dscp_marking"
            },
            {
              "direction": "egress",
              "id": "6",
              "min_kbps": 128,
              "qos_policy_id": "2",
              "type": "minimum_bandwidth"
            },
            {
              "direction": "egress",
              "id": "6",
              "min_kbps": 1000,
              "qos_policy_id": "2",
              "type": "minimum_packet_rate"
            }
          ],
          "shared": false,
          "tags": [],
          "tenant_id": "54",
          "updated_at": "2021-09-15T07:38:49.000Z"
        }
      };
    }));

    function testInitWorkflow() {
      var deferred = $q.defer();
      spyOn(neutronAPI, 'getQosPolicy').and.returnValue(deferred.promise);
      var config = workflow.init(policies.data);
      deferred.resolve(policies);
      neutronAPI.getQosPolicy(policies.data.id).then(workflow.modifyPolicies);
      $scope.$apply();
      expect(neutronAPI.getQosPolicy).toHaveBeenCalled();
      expect(config.schema).toBeDefined();
      expect(config.form).toBeDefined();
      expect(config.model).toBeDefined();
      return config;
    }

    it('should create workflow config for select rule for deleting', function() {
      testInitWorkflow();
    });

  });
})();
