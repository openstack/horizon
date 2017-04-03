/*
 * Copyright 2017 Ericsson
 *
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

  describe('trunk actions module', function() {
    var registry;
    beforeEach(module('horizon.app.core.trunks.actions'));

    beforeEach(inject(function($injector) {
      registry = $injector.get('horizon.framework.conf.resource-type-registry.service');
    }));

    it('registers Delete Trunk as an item action', function() {
      var actions = registry.getResourceType('OS::Neutron::Trunk').itemActions;
      expect(actionHasId(actions, 'deleteTrunkAction')).toBe(true);
    });

    it('registers Delete Trunk as a batch action', function() {
      var actions = registry.getResourceType('OS::Neutron::Trunk').batchActions;
      expect(actionHasId(actions, 'batchDeleteTrunkAction')).toBe(true);
    });

    it('registers Create Trunk as global action', function() {
      var actions = registry.getResourceType('OS::Neutron::Trunk').globalActions;
      expect(actionHasId(actions, 'createTrunkAction')).toBe(true);
    });

    function actionHasId(list, value) {
      return list.filter(matchesId).length === 1;

      function matchesId(action) {
        return action.id === value;
      }
    }

  });

})();
