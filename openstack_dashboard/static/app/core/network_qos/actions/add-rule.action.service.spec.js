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

  describe('horizon.app.core.network_qos.actions.add-rule.service', function() {

    var $q, $scope, neutronAPI, service, modalFormService, toast, nbwdLmtRule,
      qosPolicy, dscpRule, minBwdRule, bwdLmtRule, policyAPI, minpckRtRule;

      ///////////////////////

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.network_qos'));

    beforeEach(inject(function($injector, _$rootScope_, _$q_) {
      $scope = _$rootScope_.$new();
      $q = _$q_;
      service = $injector.get('horizon.app.core.network_qos.actions.add-rule.service');
      toast = $injector.get('horizon.framework.widgets.toast.service');
      policyAPI = $injector.get('horizon.app.core.openstack-service-api.policy');
      modalFormService = $injector.get('horizon.framework.widgets.form.ModalFormService');
      neutronAPI = $injector.get('horizon.app.core.openstack-service-api.neutron');
      qosPolicy = {model: {id: '1', name: 'qos', description: "qos rules", shared: 'yes'}};
      dscpRule = {model: {qospolicy: '1', rule_type: "dscp_marking", dscpmarking: 0}};
      minBwdRule = {
        model: {
          qospolicy: '1', rule_type: "minimum_bandwidth",
          minkbps: 128, direction: "egress"
        }};
      minpckRtRule = {
        model: {
          qospolicy: '1', rule_type: "minimum_packet_rate",
          minkpps: 1000, direction: "egress"
        }};
      bwdLmtRule = {
        model: {
          qospolicy: '1', rule_type: "bandwidth_limit",
          maxkbps: 1000, direction: "egress", maxburstkbps: 1100
        }};
      nbwdLmtRule = {
        model: {
          qospolicy: '1', rule_type: "bandwidth_limit",
          maxkbps: 1000, direction: undefined, maxburstkbps: 1100
        }};
    }));

    it('should check policy is allowed or not', function() {
      spyOn(policyAPI, 'ifAllowed').and.callThrough();
      var allowed = service.allowed();
      expect(allowed).toBeTruthy();
      expect(policyAPI.ifAllowed).toHaveBeenCalledWith(
        { rules: [['network', 'create_policy_dscp_marking_rule'],
        ['network', 'create_policy_minimum_bandwidth_rule'],
        ['network', 'create_policy_bandwidth_limit_rule']] });
    });

    it('should open the modal for selecting rule', function() {
      spyOn(modalFormService, 'open').and.returnValue($q.defer().promise);
      service.perform(qosPolicy);
      expect(modalFormService.open).toHaveBeenCalled();
    });

    it('should submit DSCP Marking add rule request to neutron', function() {
      var deferred = $q.defer();
      var data = {"dscp_mark": 0};
      spyOn(toast, 'add').and.callFake(angular.noop);
      spyOn(neutronAPI, 'createDSCPMarkingRule').and.returnValue(deferred.promise);
      deferred.resolve({data: {dscp_mark: 0, id: '1'}});
      service.submit(dscpRule).then(service.onAddRule);
      $scope.$apply();
      expect(neutronAPI.createDSCPMarkingRule).toHaveBeenCalledWith(
          '1', data);
      expect(toast.add).toHaveBeenCalledWith(
        'success', 'QoS Policy Rule successfully created'
      );
    });

    it('should submit Minimum Bandwidth add rule request to neutron', function() {
      var deferred = $q.defer();
      var data = {"min_kbps": 128, "direction": "egress"};
      spyOn(neutronAPI, 'createMinimumBandwidthRule').and.returnValue(deferred.promise);
      spyOn(toast, 'add').and.callFake(angular.noop);
      deferred.resolve({data: {mainbps: 128, direction: "egress", id:'1'}});
      service.submit(minBwdRule).then(service.onAddRule);
      $scope.$apply();
      expect(neutronAPI.createMinimumBandwidthRule).toHaveBeenCalledWith(
          '1', data);
      expect(toast.add).toHaveBeenCalledWith(
        'success', 'QoS Policy Rule successfully created'
      );
    });

    it('should submit Bandwidth Limit add rule request to neutron', function() {
      var deferred = $q.defer();
      var data = {"max_kbps": 1000, "direction": "egress", "max_burst_kbps": 1100};
      spyOn(neutronAPI, 'createBandwidthLimitRule').and.returnValue(deferred.promise);
      spyOn(toast, 'add').and.callFake(angular.noop);
      deferred.resolve({data: {"max_kbps": 1000, "direction": "egress",
          "max_burst_kbps": 1100, id: '1'}});
      service.submit(bwdLmtRule).then(service.onAddRule);
      $scope.$apply();
      expect(neutronAPI.createBandwidthLimitRule).toHaveBeenCalledWith(
          '1', data);
      expect(toast.add).toHaveBeenCalledWith(
        'success', 'QoS Policy Rule successfully created'
      );
    });

    it('should submit Bandwidth Limit with undefined add rule request to neutron', function() {
      var deferred = $q.defer();
      var data = {"max_kbps": 1000, "direction": "egress", "max_burst_kbps": 1100};
      spyOn(neutronAPI, 'createBandwidthLimitRule').and.returnValue(deferred.promise);
      spyOn(toast, 'add').and.callFake(angular.noop);
      deferred.resolve({data: {"max_kbps": 1000, "direction": "egress",
          "max_burst_kbps": 1100, id: '1'}});
      service.submit(nbwdLmtRule).then(service.onAddRule);
      $scope.$apply();
      expect(neutronAPI.createBandwidthLimitRule).toHaveBeenCalledWith(
          '1', data);
      expect(toast.add).toHaveBeenCalledWith(
        'success', 'QoS Policy Rule successfully created'
      );
    });

    it('should submit add Minimum Packet Rate rule request to neutron', function() {
      var deferred = $q.defer();
      var data = {"min_kpps": 1000, "direction": "egress"};
      spyOn(neutronAPI, 'createMinimumPacketRateRule').and.returnValue(deferred.promise);
      spyOn(toast, 'add').and.callFake(angular.noop);
      deferred.resolve({data: {minkpps: 1000, direction: "egress", id:'1'}});
      service.submit(minpckRtRule).then(service.onAddRule);
      $scope.$apply();
      expect(neutronAPI.createMinimumPacketRateRule).toHaveBeenCalledWith(
          '1', data);
      expect(toast.add).toHaveBeenCalledWith(
        'success', 'QoS Policy Rule successfully created'
      );
    });

  });
})();
