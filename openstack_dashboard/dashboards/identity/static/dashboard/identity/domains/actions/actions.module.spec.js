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

(function () {
  'use strict';

  describe('domains actions module', function() {
    var registry;
    beforeEach(module('horizon.dashboard.identity.domains.actions'));

    beforeEach(inject(function($injector) {
      registry = $injector.get('horizon.framework.conf.resource-type-registry.service');
    }));

    it('registers Create Domain as a global action', function() {
      var actions = registry.getResourceType('OS::Keystone::Domain').globalActions;
      expect(actionHasId(actions, 'createDomainAction')).toBe(true);
    });

    it('registers Delete Domains as a batch action', function() {
      var actions = registry.getResourceType('OS::Keystone::Domain').batchActions;
      expect(actionHasId(actions, 'deleteDomainsAction')).toBe(true);
    });

    it('registers Delete Domain as a item action', function() {
      var actions = registry.getResourceType('OS::Keystone::Domain').itemActions;
      expect(actionHasId(actions, 'deleteDomainAction')).toBe(true);
    });

    function actionHasId(list, value) {
      return list.filter(matchesId).length === 1;

      function matchesId(action) {
        if (action.id === value) {
          return true;
        }
      }
    }

  });

})();
