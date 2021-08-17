/* Liscensed under the Apache License, Version 2.0 (the "License");
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

  describe('horizon.app.core.network_qos.actions.delete-rule.service', function() {

    var $q, $scope, neutronAPI, service, modalFormService, toast, nqosPolicy, edscpRule,
      qosPolicy, dscpRule, bwdLmtRule, minBwdRule, policyAPI;

      ///////////////////////

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.network_qos'));

    beforeEach(inject(function($injector, _$rootScope_, _$q_) {
      $scope = _$rootScope_.$new();
      $q = _$q_;
      service = $injector.get('horizon.app.core.network_qos.actions.delete-rule.service');
      toast = $injector.get('horizon.framework.widgets.toast.service');
      policyAPI = $injector.get('horizon.app.core.openstack-service-api.policy');
      modalFormService = $injector.get('horizon.framework.widgets.form.ModalFormService');
      neutronAPI = $injector.get('horizon.app.core.openstack-service-api.neutron');
      qosPolicy = {
        "id": "6",
        "name": "qos",
        "description": "qos rules",
        "shared": "yes",
        "rules": [
          {
            "direction": "egress",
            "id": "8",
            "max_burst_kbps": 22000,
            "max_kbps": 20000,
            "qos_policy_id": "6",
            "type": "bandwidth_limit"
          },
          {
            "dscp_mark": 26,
            "id": "5",
            "qos_policy_id": "6",
            "type": "dscp_marking"
          },
          {
            "direction": "egress",
            "id": "2",
            "min_kbps": 1000,
            "qos_policy_id": "6",
            "type": "minimum_bandwidth"
          }
        ]
      };
      nqosPolicy = {
        "id": "6",
        "name": "qos",
        "description": "qos rules",
        "shared": "yes",
        "rules": []
      };
      dscpRule = {
        "model": {
          "qospolicy": "6",
          "qospolicyname": "test",
          "ruleid": "2",
          "rules": [
            {
              "dscp_mark": 0,
              "id": "2",
              "qos_policy_id": "6",
              "type": "dscp_marking"
            }
          ]
        }
      };
      edscpRule = {
        "model": {
          "qospolicy": "6",
          "qospolicyname": "test",
          "ruleid": "3",
          "rules": [
            {
              "dscp_mark": 0,
              "id": "2",
              "qos_policy_id": "6",
              "type": "dscp_marking"
            }
          ]
        }
      };
      minBwdRule = {
        "model": {
          "qospolicy": "6",
          "qospolicyname": "test",
          "ruleid": "2",
          "rules": [
            {
              "min_kbps": 0,
              "direction": "egress",
              "id": 2,
              "qos_policy_id": "6",
              "type": "minimum_bandwidth"
            }
          ]
        }
      };
      bwdLmtRule = {
        "model": {
          "qospolicy": "6",
          "qospolicyname": "test",
          "ruleid": "2",
          "rules": [
            {
              "max_kbps": 0,
              "direction": "egress",
              "id": 2,
              "qos_policy_id": "6",
              "type": "bandwidth_limit"
            }
          ]
        }
      };
    }));

    it('should check policy is allowed or not', function() {
      spyOn(policyAPI, 'ifAllowed').and.callThrough();
      var allowed = service.allowed();
      expect(allowed).toBeTruthy();
      expect(policyAPI.ifAllowed).toHaveBeenCalledWith(
        { rules: [['network', 'delete_policy_bandwidth_limit_rule'],
        ['network', 'delete_policy_dscp_marking_rule'],
        ['network', 'delete_policy_minimum_bandwidth_rule']] });
    });

    it('should open the modal with existing rule', function() {
      spyOn(modalFormService, 'open').and.returnValue($q.defer().promise);

      service.perform(qosPolicy);

      expect(modalFormService.open).toHaveBeenCalled();
    });

    it('should not open the modal', function() {
      spyOn(modalFormService, 'open').and.returnValue($q.defer().promise);
      spyOn(toast, 'add').and.callFake(angular.noop);

      service.perform(nqosPolicy);

      expect(modalFormService.open).not.toHaveBeenCalled();
      expect(toast.add).toHaveBeenCalledWith(
        'info', 'There are no rules to delete.'
      );
    });

    it('should submit DSCP Marking delete rule request to neutron', function() {
      var deferred = $q.defer();
      spyOn(toast, 'add').and.callFake(angular.noop);
      spyOn(neutronAPI, 'deleteDSCPMarkingRule').and.returnValue(deferred.promise);
      deferred.resolve({data: {"id": "2", "dscp_mark": 12}});
      service.submit(dscpRule).then(service.success);
      $scope.$apply();
      expect(neutronAPI.deleteDSCPMarkingRule).toHaveBeenCalledWith(
          qosPolicy.id, [dscpRule.model.ruleid]);
      expect(toast.add).toHaveBeenCalledWith(
        'success', 'Qos Policy  Rule  was successfully deleted.'
      );
    });

    it('should submit DSCP Marking check delete rule request to neutron', function() {
      var deferred = $q.defer();
      spyOn(toast, 'add').and.callFake(angular.noop);
      spyOn(neutronAPI, 'deleteDSCPMarkingRule').and.returnValue(deferred.promise);
      deferred.resolve({data: {"id": "3", "dscp_mark": 0}});
      service.submit(edscpRule);
      $scope.$apply();
      expect(neutronAPI.deleteDSCPMarkingRule).not.toHaveBeenCalledWith(
          qosPolicy.id, [dscpRule.model.ruleid]);
      expect(toast.add).not.toHaveBeenCalledWith(
        'success', 'Qos Policy  Rule  was successfully deleted.'
      );
    });

    it('should submit Bandwidth Limit delete rule request to neutron', function() {
      var deferred = $q.defer();
      spyOn(toast, 'add').and.callFake(angular.noop);
      spyOn(neutronAPI, 'deleteBandwidthLimitRule').and.returnValue(deferred.promise);
      deferred.resolve({data: {"id": "2", "max_kbps": 1000, "direction": "ingress",
          "max_burst_kbps": 1200}});
      service.submit(bwdLmtRule).then(service.onDeleteRule);
      $scope.$apply();
      expect(neutronAPI.deleteBandwidthLimitRule).toHaveBeenCalledWith(
          qosPolicy.id, [bwdLmtRule.model.ruleid]);
      expect(toast.add).toHaveBeenCalledWith(
        'success', 'Qos Policy  Rule  was successfully deleted.'
      );
    });

    it('should submit Minimum Bandwidth Limit edit rule request to neutron', function() {
      var deferred = $q.defer();
      spyOn(toast, 'add').and.callFake(angular.noop);
      spyOn(neutronAPI, 'deleteMinimumBandwidthRule').and.returnValue(deferred.promise);
      deferred.resolve({data: {"id": "2", "min_kbps": 100, "direction": "ingress"}});
      service.submit(minBwdRule).then(service.success);
      $scope.$apply();
      expect(neutronAPI.deleteMinimumBandwidthRule).toHaveBeenCalledWith(
          qosPolicy.id, [minBwdRule.model.ruleid]);
      expect(toast.add).toHaveBeenCalledWith(
        'success', 'Qos Policy  Rule  was successfully deleted.'
      );
    });

  });
})();
