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

  describe('horizon.app.core.network_qos.actions.edit-rule.service', function() {

    var $q, $scope, neutronAPI, service, modalFormService, toast, nqosPolicy,
      qosPolicy, dscpRule, bwdLmtRule, minBwdRule, policyAPI, minPckRtRule;

      ///////////////////////

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.network_qos'));

    beforeEach(inject(function($injector, _$rootScope_, _$q_) {
      $scope = _$rootScope_.$new();
      $q = _$q_;
      service = $injector.get('horizon.app.core.network_qos.actions.edit-rule.service');
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
          },
          {
            "direction": "egress",
            "id": "2",
            "min_kbps": 10000,
            "qos_policy_id": "6",
            "type": "minimum_packet_rate"
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
          "rule_type": "dscp_marking",
          "dscpmarking": 26,
          "rules": [
            {
              "dscp_mark": 0,
              "id": 2,
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
          "rule_type": "minimum_bandwidth",
          "minkbps": 128,
          "direction": "egress",
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
          "rule_type": "bandwidth_limit",
          "maxkbps": 1000,
          "maxburstkbps": 1100,
          "direction": "egress",
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
      minPckRtRule = {
        "model": {
          "qospolicy": "6",
          "qospolicyname": "test",
          "ruleid": "2",
          "rule_type": "minimum_packet_rate",
          "minkpps": 20000,
          "direction": "ingress",
          "rules": [
            {
              "min_kpps": 10000,
              "direction": "egress",
              "id": 2,
              "qos_policy_id": "6",
              "type": "minimum_packet_rate"
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
        { rules: [['network', 'update_policy_bandwidth_limit_rule'],
        ['network', 'update_policy_dscp_marking_rule'],
        ['network', 'update_policy_minimum_bandwidth_rule']] });
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
        'info', 'There are no rules to modify.'
      );
    });

    it('should submit DSCP Marking edit rule request to neutron', function() {
      var deferred = $q.defer();
      var data = {"dscp_mark": 26};
      spyOn(toast, 'add').and.callFake(angular.noop);
      spyOn(neutronAPI, 'updateDSCPMarkingRule').and.returnValue(deferred.promise);
      deferred.resolve({data: {dscp_mark: 26, id: '2'}});
      service.submit(dscpRule).then(service.success);
      $scope.$apply();
      expect(neutronAPI.updateDSCPMarkingRule).toHaveBeenCalledWith(
          qosPolicy.id, [dscpRule.model.ruleid], data);
      expect(toast.add).toHaveBeenCalledWith(
        'success', 'Qos Policy Rule 2 was successfully updated.'
      );
    });

    it('should submit Bandwidth Limit edit rule request to neutron', function() {
      var deferred = $q.defer();
      var data = {"max_kbps": 1000, "direction": "egress", "max_burst_kbps": 1100};
      spyOn(toast, 'add').and.callFake(angular.noop);
      spyOn(neutronAPI, 'updateBandwidthRule').and.returnValue(deferred.promise);
      deferred.resolve({data: {"id": "2", "max_kbps": 1000, "direction": "egress",
        "max_burst_kbps": 1100}});
      service.submit(bwdLmtRule).then(service.success);
      $scope.$apply();
      expect(neutronAPI.updateBandwidthRule).toHaveBeenCalledWith(
          qosPolicy.id, [bwdLmtRule.model.ruleid], data);
      expect(toast.add).toHaveBeenCalledWith(
        'success', 'Qos Policy Rule 2 was successfully updated.'
      );
    });

    it('should submit Minimum BandwidthLimit edit rule request to neutron', function() {
      var deferred = $q.defer();
      var data = {"min_kbps": 128, "direction": "egress"};
      spyOn(toast, 'add').and.callFake(angular.noop);
      spyOn(neutronAPI, 'updateMinimumBandwidthRule').and.returnValue(deferred.promise);
      deferred.resolve({data: {"id": "2", "min_kbps": 128, "direction": "egress"}});
      service.submit(minBwdRule).then(service.success);
      $scope.$apply();
      expect(neutronAPI.updateMinimumBandwidthRule).toHaveBeenCalledWith(
          qosPolicy.id, [minBwdRule.model.ruleid], data);
      expect(toast.add).toHaveBeenCalledWith(
        'success', 'Qos Policy Rule 2 was successfully updated.'
      );
    });

    it('should submit Minimum Packet Rate edit rule request to neutron', function() {
      var deferred = $q.defer();
      var data = {"min_kpps": 20000, "direction": "ingress"};
      spyOn(toast, 'add').and.callFake(angular.noop);
      spyOn(neutronAPI, 'updateMinimumPacketRateRule').and.returnValue(deferred.promise);
      deferred.resolve({data: {"id": "2", "min_kpps": 20000, "direction": "ingress"}});
      service.submit(minPckRtRule).then(service.success);
      $scope.$apply();
      expect(neutronAPI.updateMinimumPacketRateRule).toHaveBeenCalledWith(
          qosPolicy.id, [minPckRtRule.model.ruleid], data);
      expect(toast.add).toHaveBeenCalledWith(
        'success', 'Qos Policy Rule 2 was successfully updated.'
      );
    });

  });
})();
