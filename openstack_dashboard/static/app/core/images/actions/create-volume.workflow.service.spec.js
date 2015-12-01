/**
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use self file except in compliance with the License. You may obtain
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

  describe('horizon.app.core.images.actions.createVolumeWorkflow', function() {

    var mockWorkflow = function(params) {
      return params;
    };

    var service;

    ///////////////////////

    beforeEach(module('horizon.framework.util'));

    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.workflow', function($provide) {
      $provide.value('horizon.app.core.workflow.factory', mockWorkflow);
    }));

    beforeEach(module('horizon.app.core.images', function($provide) {
      $provide.constant('horizon.app.core.images.basePath', '/dummy/');
    }));

    beforeEach(inject(function($injector) {
      service = $injector.get('horizon.app.core.images.actions.createVolumeWorkflow');
    }));

    it('create the workflow for creating a volume', function() {
      expect(service.title).toEqual('Create Volume');
      expect(service.steps.length).toEqual(1);
      expect(service.steps[0].templateUrl).toEqual('/dummy/steps/create-volume/create-volume.html');
    });

  });

})();
