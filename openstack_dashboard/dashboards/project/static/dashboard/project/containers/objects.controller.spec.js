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

  describe('horizon.dashboard.project.containers objects controller', function() {
    var $routeParams, controller, model;

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core.openstack-service-api'));

    beforeEach(module('horizon.dashboard.project.containers', function before($provide) {
      $routeParams = {};
      $provide.value('$routeParams', $routeParams);
    }));

    beforeEach(inject(function ($injector) {
      controller = $injector.get('$controller');
      model = $injector.get('horizon.dashboard.project.containers.containers-model');
    }));

    function createController() {
      return controller('horizon.dashboard.project.containers.ObjectsController', {
        'horizon.dashboard.project.containers.containerRoute': 'eggs/'
      });
    }

    it('should load contents', function test () {
      spyOn(model, 'selectContainer');
      $routeParams.containerName = 'spam';
      var ctrl = createController();

      expect(ctrl.containerURL).toEqual('eggs/spam/');
      expect(ctrl.currentURL).toEqual('eggs/spam/');

      expect(model.selectContainer).toHaveBeenCalledWith('spam', undefined);
    });

    it('should handle subfolders', function test () {
      spyOn(model, 'selectContainer');
      $routeParams.containerName = 'spam';
      $routeParams.folder = 'ham';
      var ctrl = createController();

      expect(ctrl.containerURL).toEqual('eggs/spam/');
      expect(ctrl.currentURL).toEqual('eggs/spam/ham/');

      expect(model.selectContainer).toHaveBeenCalledWith('spam', 'ham');
    });
  });
})();
