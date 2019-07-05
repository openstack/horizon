/**
 *
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

  describe('flavor actions module', function() {
    var registry;
    beforeEach(module('horizon.app.core.flavors.actions'));

    beforeEach(inject(function($injector) {
      registry = $injector.get('horizon.framework.conf.resource-type-registry.service');
    }));

    it('registers Delete Flavor as a batch action', function() {
      var actions = registry.getResourceType('OS::Nova::Flavor').batchActions;
      expect(actionHasId(actions, 'batchDeleteFlavorAction')).toBe(true);
    });

    it('registers Delete Flavor as a item action', function() {
      var actions = registry.getResourceType('OS::Nova::Flavor').itemActions;
      expect(actionHasId(actions, 'deleteFlavorAction')).toBe(true);
    });

    it('registers Update Metadata as a batch action', function() {
      var actions = registry.getResourceType('OS::Nova::Flavor').itemActions;
      expect(actionHasId(actions, 'updateMetadataService')).toBe(true);
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
