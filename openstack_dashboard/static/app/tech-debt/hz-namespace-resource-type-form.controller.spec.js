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

  describe('horizon.app.tech-debt.hzNamespaceResourceTypeFormController', function() {

    var $window, controller;

    beforeEach(module('horizon.app.tech-debt'));
    beforeEach(inject(function($injector) {
      controller = $injector.get('$controller');
      $window = $injector.get('$window');
    }));

    function createController() {
      return controller('hzNamespaceResourceTypeFormController', {});
    }

    it('should set resource_types', function() {
      $window.resource_types = [1];

      var ctrl = createController();
      expect(ctrl.resource_types).toEqual([1]);
    });

    it('should save resource_types', function() {
      $window.resource_types = [1];

      var ctrl = createController();
      ctrl.saveResourceTypes();

      expect(ctrl.resource_types).toEqual('[1]');
    });

  });
})();
