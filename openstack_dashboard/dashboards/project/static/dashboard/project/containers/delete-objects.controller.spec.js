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

  describe('horizon.dashboard.project.containers delete-objects controller', function() {
    beforeEach(module('horizon.app.core.openstack-service-api'));
    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.dashboard.project'));

    var $q, $rootScope, collectDeferred, controller, model;
    var $uibModalInstance = {
      dismiss: angular.noop,
      close: angular.noop
    };

    beforeEach(module('horizon.dashboard.project.containers'));

    beforeEach(inject(function ($injector, _$q_, _$rootScope_) {
      controller = $injector.get('$controller');
      $q = _$q_;
      $rootScope = _$rootScope_;
      model = $injector.get('horizon.dashboard.project.containers.containers-model');
      collectDeferred = $q.defer();
      spyOn(model, 'recursiveCollect').and.returnValue(collectDeferred.promise);
    }));

    function createController(selected) {
      return controller('DeleteObjectsModalController', {
        $uibModalInstance: $uibModalInstance,
        selected: selected
      });
    }

    it('should set the local model', function() {
      var ctrl = createController(['one']);
      expect(ctrl.model).toBeDefined();
    });

    it('should invoke recursiveCollect when created', function() {
      var files = [
        {name: 'one'},
        {name: 'two'},
        {name: 'three'}
      ];
      var ctrl = createController(files);
      expect(ctrl.model.running).toEqual(true);
      expect(model.recursiveCollect).toHaveBeenCalledWith(ctrl.model, files,
        ctrl.model.collection);
      collectDeferred.resolve();
      $rootScope.$apply();
      expect(ctrl.model.running).toEqual(false);
    });

    it('should cancel collection on dismiss', function() {
      spyOn($uibModalInstance, 'dismiss');

      var ctrl = createController([]);
      expect(ctrl.model.cancel).toEqual(false);
      ctrl.dismiss();

      expect(ctrl.model.cancel).toEqual(true);
      expect($uibModalInstance.dismiss).toHaveBeenCalled();
    });

    it('should close perform delete on OK after collection', function() {
      spyOn($uibModalInstance, 'close');

      var ctrl = createController([]);
      ctrl.model.mode = 'deletion';
      ctrl.action();

      expect($uibModalInstance.close).toHaveBeenCalled();
    });

    it('should close dialog on OK after delete', function() {
      var deferred = $q.defer();
      spyOn(model, 'recursiveDelete').and.returnValue(deferred.promise);
      spyOn($uibModalInstance, 'close');

      var ctrl = createController([]);
      ctrl.model.mode = 'discovery';
      ctrl.model.collection = ['one'];
      ctrl.action();

      expect(model.recursiveDelete).toHaveBeenCalledWith(ctrl.model, {tree: ['one']});
      expect(ctrl.model.mode).toEqual('deletion');
      expect(ctrl.model.running).toEqual(true);

      deferred.resolve();
      $rootScope.$apply();

      expect(ctrl.model.running).toEqual(false);
    });
  });
})();
