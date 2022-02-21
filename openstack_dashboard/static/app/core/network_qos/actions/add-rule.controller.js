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

  /**
   * @ngdoc controller
   * @name horizon.app.core.network_qos.actions.AddQoSRuleController
   * @ngController
   *
   * @description
   * Controller for the adding rules for qos policy
   */
  angular
    .module('horizon.app.core.network_qos.actions')
    .controller('horizon.app.core.network_qos.actions.AddQoSRuleController',
      addQoSRuleController);

  addQoSRuleController.$inject = [
    '$scope'
  ];

  function addQoSRuleController($scope) {
    var ctrl = this;
    ctrl.qospolicy = $scope.model.qospolicy;
    ctrl.qospolicyname = $scope.model.qospolicyname;
    ctrl.rule_types = {
      'bandwidth_limit': gettext("Bandwidth Limit"),
      'dscp_marking': gettext("DSCP Marking"),
      'minimum_bandwidth': gettext("Minimum Bandwidth"),
      'minimum_packet_rate': gettext("Minimum Packet Rate")
    };
    ctrl.directions = {
      "egress": gettext("egress"),
      "ingress": gettext("ingress")
    };
    ctrl.ppsDirections = {
      "egress": gettext("egress"),
      "ingress": gettext("ingress"),
      "any": gettext("any")
    };
    ctrl.onRuleTypeChange = function(ruleType) {
      $scope.model.rule_type = ruleType;
    };
    ctrl.bwdLimit = function(bwd) {
      $scope.model.maxkbps = bwd.maxkbps;
      $scope.model.maxburstkbps = bwd.maxburstkbps;
      $scope.model.direction = bwd.direction || 'egress';
    };
    ctrl.onDSCPChange = function(dscpmark) {
      $scope.model.dscpmarking = dscpmark;
    };
    ctrl.minBandwidth = function(mb) {
      $scope.model.minkbps = mb.minkbps;
      $scope.model.direction = mb.direction || 'egress';
    };
    ctrl.minPacketRate = function(mpr) {
      $scope.model.minkpps = mpr.minkpps;
      $scope.model.direction = mpr.direction || 'egress';
    };
  }
})();
