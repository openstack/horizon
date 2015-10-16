/**
 * (c) Copyright 2016 Hewlett-Packard Development Company, L.P.
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

  describe('horizon.app.core.images edit image controller', function() {

    var controller, $scope, events, $q, settingsCall, $timeout;

    ///////////////////////

    beforeEach(module('horizon.framework'));

    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.images'));

    beforeEach(inject(function ($injector, _$rootScope_, _$q_, _$timeout_) {
      $scope = _$rootScope_.$new();
      $q = _$q_;
      $timeout = _$timeout_;

      events = $injector.get('horizon.app.core.images.events');
      controller = $injector.get('$controller');
    }));

    function createController() {
      var settings = {
        getSettings: function() {
          settingsCall = $q.defer();
          return settingsCall.promise;
        }
      };
      return controller('horizon.app.core.images.steps.EditImageController as ctrl', {
        $scope: $scope,
        events: events,
        'horizon.app.core.openstack-service-api.settings': settings
      });
    }

    function setImagePromise(image) {
      var deferred = $q.defer();
      deferred.resolve({data: image});
      $scope.imagePromise = deferred.promise;
    }

    it('should have options for visibility and protected', function() {
      setImagePromise({id: '1', container_format: 'bare', is_public: false, properties: []});
      var ctrl = createController();

      expect(ctrl.imageVisibilityOptions.length).toEqual(2);
      expect(ctrl.imageProtectedOptions.length).toEqual(2);
    });

    it('should map is_public', function() {
      setImagePromise({id: '1', container_format: 'bare', is_public: false, properties: []});
      var ctrl = createController();
      $timeout.flush();

      expect(ctrl.image.visibility).toEqual('private');
    });

    it('reads the data format settings', function() {
      setImagePromise({id: '1', container_format: 'bare', is_public: false, properties: []});
      var ctrl = createController();
      settingsCall.resolve({OPENSTACK_IMAGE_FORMATS: ['aki', 'ami']});
      $timeout.flush();
      expect(ctrl.imageFormats.aki).toBeDefined();
      expect(ctrl.imageFormats.ami).toBeDefined();
      expect(Object.keys(ctrl.imageFormats).length).toBe(2);
    });

    it('should initialize image values correctly', function() {
      setImagePromise({
        id: '1',
        container_format: 'bare',
        disk_format: 'ova',
        is_public: true,
        properties: []
      });
      var ctrl = createController();
      $timeout.flush();

      expect(ctrl.image.disk_format).toEqual('ova');
      expect(ctrl.image.visibility).toEqual('public');
    });

    it('should set local image_format to docker when container is docker', function() {
      setImagePromise({id: '1', disk_format: 'raw', container_format: 'docker',
        is_public: false, properties: []});
      var ctrl = createController();
      $timeout.flush();

      expect(ctrl.image_format).toEqual('docker');
    });

    it('should set container to aki when disk format is same', function() {
      setImagePromise({id: '1', disk_format: 'aki', container_format: '',
        is_public: false, properties: []});
      var ctrl = createController();
      $timeout.flush();

      expect(ctrl.image.container_format).toEqual('aki');
    });

    it('should set container to ami when disk format is same', function() {
      setImagePromise({id: '1', disk_format: 'ami', container_format: '',
        is_public: false, properties: []});
      var ctrl = createController();
      $timeout.flush();

      expect(ctrl.image.container_format).toEqual('ami');
    });

    it('should set container to ari when disk format is same', function() {
      setImagePromise({id: '1', disk_format: 'ari', container_format: '',
        is_public: false, properties: []});
      var ctrl = createController();
      $timeout.flush();

      expect(ctrl.image.container_format).toEqual('ari');
    });

    it("should destroy the image changed watcher when the controller is destroyed", function() {
      setImagePromise({id: '1', container_format: 'bare', properties: []});
      spyOn($scope, '$emit').and.callThrough();

      var ctrl = createController();
      ctrl.image = 1;
      $scope.$apply();

      $scope.$emit("$destroy");
      $scope.$emit.calls.reset();

      ctrl.image = 2;
      $scope.$apply();

      expect($scope.$emit).not.toHaveBeenCalled();
    });

  });
})();
