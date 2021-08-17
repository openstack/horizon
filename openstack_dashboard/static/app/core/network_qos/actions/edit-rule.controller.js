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
   * @name horizon.app.core.network_qos.actions.EditQoSRuleController
   * @ngController
   *
   * @description
   * Controller for the editing rules for qos policy
   */
  angular
    .module('horizon.app.core.network_qos.actions')
    .controller('horizon.app.core.network_qos.actions.EditQoSRuleController',
      editQoSRuleController);

  editQoSRuleController.$inject = [
    '$scope'
  ];

  function editQoSRuleController($scope) {
    var ctrl = this;
    ctrl.qospolicy = $scope.model.qospolicy;
    ctrl.qospolicyname = $scope.model.qospolicyname;
    ctrl.rule_types = [];
    angular.forEach($scope.model.rules, function(k) {
      if (k.type === 'bandwidth_limit') {
        ctrl.rule_types.push({name: 'bandwidth_limit', val: gettext('Bandwidth Limit - ' +
          k.id + ', ' + k.max_kbps + ', ' + k.max_burst_kbps + ', ' + k.direction)});
        ctrl.bwdid = k.id;
        ctrl.maxkbps = k.max_kbps;
        ctrl.maxburstkbps = k.max_burst_kbps || 0;
        ctrl.bwddirection = k.direction;
      }
      else if (k.type === 'dscp_marking') {
        ctrl.rule_types.push({name: 'dscp_marking',
          val: gettext("DSCP Mark - " + k.id + ', ' + k.dscp_mark)});
        ctrl.dscpid = k.id;
        ctrl.dscpmark = k.dscp_mark;
      }
      else if (k.type === 'minimum_bandwidth') {
        ctrl.rule_types.push({name: 'minimum_bandwidth',
          val: gettext('Minimum Bandwidth - ' + k.id + ', ' + k.min_kbps + ', ' + k.direction)});
        ctrl.minbwdid = k.id;
        ctrl.minkbps = k.min_kbps;
        ctrl.minbwddirection = k.direction;
      }
      else if (k.type === 'minimum_packet_rate') {
        ctrl.rule_types.push({name: 'minimum_packet_rate',
          val: gettext('Minimum Packet Rate - ' + k.id + ', ' + k.min_kpps + ', ' +
          k.direction)});
        ctrl.minpckrtid = k.id;
        ctrl.minkpps = k.min_kpps;
        ctrl.minpckrtdirection = k.direction;
      }
    }, this);
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
      $scope.model.rule_type = ruleType.name;
    };
    ctrl.bwdLimit = function(bwd) {
      $scope.model.ruleid = ctrl.bwdid;
      $scope.model.maxkbps = bwd.maxkbps || ctrl.maxkbps;
      $scope.model.maxburstkbps = bwd.maxburstkbps || ctrl.maxburstkbps;
      $scope.model.direction = bwd.direction || ctrl.bwddirection;
    };
    ctrl.onDSCPChange = function(dscpmark) {
      $scope.model.ruleid = ctrl.dscpid;
      $scope.model.dscpmarking = dscpmark || ctrl.dscpmark;
    };
    ctrl.minBandwidth = function(mb) {
      $scope.model.ruleid = ctrl.minbwdid;
      $scope.model.minkbps = mb.minkbps || ctrl.minkbps;
      $scope.model.direction = mb.direction || ctrl.minbwddirection;
    };
    ctrl.minPacketRate = function(mpr) {
      $scope.model.ruleid = ctrl.minpckrtid;
      $scope.model.minkpps = mpr.minkpps || ctrl.minkpps;
      $scope.model.direction = mpr.direction || ctrl.minpckrtdirection;
    };
  }
})();
