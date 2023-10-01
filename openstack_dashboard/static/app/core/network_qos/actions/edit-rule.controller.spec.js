/*
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

  describe('qos rules datails', function() {

    var ctrl, rules, directions, ppsDirections, $controller, $scope,
      $rootScope, dscp, ndscp, minBwd, nminBwd, bwdLmt, nbwdLmt,
      minPckRt, nminPckRt;

    beforeEach(module('horizon.app.core.network_qos'));

    beforeEach(inject(function(_$controller_, _$rootScope_) {
      $controller = _$controller_;
      $rootScope = _$rootScope_;
      $scope = $rootScope.$new();

      $scope = {
        model: {
          qospolicy: "1",
          qospolicyname: "test_qos",
          rules: [
            {
              type: "bandwidth_limit",
              id: 1, max_kbps: 1000,
              max_burst_kbps: 100, direction: "egress"
            },
            {
              type: "dscp_marking",
              id: 1, dscp_mark: 12
            },
            {
              type: "minimum_bandwidth",
              id: 1, min_kbps: 100,
              direction: "egress"
            },
            {
              type: "minimum_packet_rate",
              id: 1, min_kpps: 10000,
              direction: "egress"
            }
          ]
        }
      };

      ctrl = $controller('horizon.app.core.network_qos.actions.EditQoSRuleController',
        {
          $scope: $scope
        }
      );

      rules = [
        {name: "bandwidth_limit",
         val: "1 - Bandwidth Limit - maxkbps: 1000, maxburstkbps: 100, egress"},
        {name: "dscp_marking",
         val: "1 - DSCP Marking - dscpmark: 12"},
        {name: "minimum_bandwidth",
         val: "1 - Minimum Bandwidth - minkbps: 100, egress"},
        {name: "minimum_packet_rate",
         val: "1 - Minimum Packet Rate - minkpps: 10000, egress"}
      ];
      directions = {
        "egress": "egress",
        "ingress": "ingress"
      };
      ppsDirections = {
        "egress": "egress",
        "ingress": "ingress",
        "any": "any"
      };
      dscp = {
        model: {
          dscpmarking: 0
        }
      };
      ndscp = {
        model: {
          dscpmarking: undefined
        }
      };
      minBwd = {
        model: {
          minkbps: 1000,
          direction: 'egress'
        }
      };
      nminBwd = {
        model: {
          minkbps: '',
          direction: ''
        }
      };
      bwdLmt = {
        model: {
          maxkbps: 2000,
          maxburstkbps: 3000,
          direction: 'egress'
        }
      };
      nbwdLmt = {
        model: {
          maxkbps: '',
          maxburstkbps: '',
          direction: ''
        }
      };
      minPckRt = {
        model: {
          minkpps: 10000,
          direction: 'egress'
        }
      };
      nminPckRt = {
        model: {
          minkpps: '',
          direction: ''
        }
      };
    }));

    it('sets edit ctrl', inject(function() {
      expect(ctrl.qospolicy).toEqual($scope.model.qospolicy);
      expect(ctrl.qospolicy).not.toEqual('2');
      expect(ctrl.rule_types).toEqual(rules);
      ctrl.onRuleTypeChange('dscp_mark');
      expect(ctrl.onRuleTypeChange).toBeDefined();
      expect(ctrl.directions).toEqual(directions);
      expect(ctrl.ppsDirections).toEqual(ppsDirections);
      // DSCP Mark
      ctrl.onDSCPChange(dscp.model);
      expect(ctrl.onDSCPChange).toBeDefined();
      ctrl.onDSCPChange(ndscp.model);
      expect(ctrl.onDSCPChange).toBeDefined();
      // Minimum Bandwidth
      ctrl.minBandwidth(minBwd.model);
      expect(ctrl.minBandwidth).toBeDefined();
      ctrl.minBandwidth(nminBwd.model);
      expect(ctrl.minBandwidth).toBeDefined();
      // Bandwidth Limit
      ctrl.bwdLimit(bwdLmt.model);
      expect(ctrl.bwdLimit).toBeDefined();
      ctrl.bwdLimit(nbwdLmt.model);
      expect(ctrl.nbwdLimit).not.toBeDefined();
      // Minimum Packet Rate
      ctrl.minPacketRate(minPckRt.model);
      expect(ctrl.minPacketRate).toBeDefined();
      ctrl.minPacketRate(nminPckRt.model);
      expect(ctrl.minPacketRate).toBeDefined();
    }));

  });
})();
