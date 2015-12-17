/**
 *    (c) Copyright 2016 Rackspace US, Inc
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

  describe('horizon.dashboard.project.containers containers controller', function() {
    beforeEach(module('horizon.app.core.openstack-service-api'));
    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.dashboard.project'));

    var $location, controller, model;

    beforeEach(inject(function ($injector) {
      controller = $injector.get('$controller');
      $location = $injector.get('$location');
      model = $injector.get('horizon.dashboard.project.containers.containers-model');
    }));

    function createController() {
      return controller(
        'horizon.dashboard.project.containers.ContainersController', {
          'horizon.dashboard.project.containers.containerRoute': 'eggs '
        });
    }

    it('should set containerRoute', function() {
      var ctrl = createController();
      expect(ctrl.containerRoute).toBeDefined();
    });

    it('should invoke initialise the model when created', function() {
      spyOn(model, 'initialize');
      createController();
      expect(model.initialize).toHaveBeenCalled();
    });

    it('should update current container name when one is selected', function () {
      spyOn($location, 'path');
      var ctrl = createController();
      ctrl.selectContainer('and spam');
      expect($location.path).toHaveBeenCalledWith('eggs and spam');
      expect(ctrl.selectedContainer).toEqual('and spam');
    });
  });
})();
