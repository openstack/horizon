/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

  describe('hz-resource-panel controller', function() {
    var ctrl;

    var resourceType = {
      getName: function() {
        return 'MyType';
      }
    };

    beforeEach(module('horizon.framework.conf'));
    beforeEach(module('horizon.framework.widgets.panel'));

    beforeEach(inject(function($controller) {
      var registry = {
        getResourceType: angular.noop
      };

      spyOn(registry, 'getResourceType').and.returnValue(resourceType);

      ctrl = $controller('horizon.framework.widgets.panel.HzResourcePanelController', {
        'horizon.framework.conf.resource-type-registry.service': registry,
        tableResourceType: 'OS::Test::Example'});
    }));

    it('exists', function() {
      expect(ctrl).toBeDefined();
    });

    it('sets resourceType to the resource type', function() {
      expect(ctrl.resourceType).toBe(resourceType);
    });

    it('sets resourceTypeName to the resource type name', function() {
      expect(ctrl.pageName).toEqual('MyType');
    });
  });

})();
