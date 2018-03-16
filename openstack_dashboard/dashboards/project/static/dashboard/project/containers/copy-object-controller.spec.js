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

  describe('horizon.dashboard.project.containers copy-object controller', function() {
    var controller, ctrl;

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.dashboard.project.containers'));

    beforeEach(module(function ($provide) {
      $provide.value('fileDetails', {
        container: 'spam',
        path: 'ham/eggs'
      });
    }));

    beforeEach(inject(function ($injector) {
      controller = $injector.get('$controller');
      ctrl = controller('horizon.dashboard.project.containers.CopyObjectModalController');
    }));

    it('should initialise the controller model when created', function test() {
      expect(ctrl.model.container).toEqual('spam');
      expect(ctrl.model.path).toEqual('ham/eggs');
      expect(ctrl.model.dest_container).toEqual('');
      expect(ctrl.model.dest_name).toEqual('');
    });
  });
})();
