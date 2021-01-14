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

  describe('horizon.app.core.images create image controller', function() {

    function fakeGlance() {
      return {
        success: function(callback) {
          callback({
            items: [
              {disk_format: 'aki'},
              {disk_format: 'ari'},
              {disk_format: ''}]
          });
        }
      };
    }

    function policyIfAllowed() {
      return {
        then: function(callback) {
          callback({allowed: true});
        }
      };
    }

    var controller, glanceAPI, $scope, events, $q, settingsCall, $timeout, policyAPI;

    ///////////////////////

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));

    beforeEach(inject(function ($injector, _$rootScope_, _$q_, _$timeout_) {
      $scope = _$rootScope_.$new();
      $scope.stepModels = {imageForm: {}, updateMetadataForm: {}};
      $q = _$q_;
      $timeout = _$timeout_;

      glanceAPI = $injector.get('horizon.app.core.openstack-service-api.glance');

      events = $injector.get('horizon.app.core.images.events');
      controller = $injector.get('$controller');

      spyOn(glanceAPI, 'getImages').and.callFake(fakeGlance);

      policyAPI = $injector.get('horizon.app.core.openstack-service-api.policy');
      spyOn(policyAPI, 'ifAllowed').and.callFake(policyIfAllowed);
    }));

    function createController() {
      var settings = {
        getSettings: function() {
          settingsCall = $q.defer();
          return settingsCall.promise;
        }
      };
      var imageFormats = {
        'a': 'apple',
        'b': 'banana',
        'c': 'cherry',
        'd': 'django'
      };
      return controller('horizon.app.core.images.steps.CreateImageController as ctrl', {
        $scope: $scope,
        glanceAPI: glanceAPI,
        events: events,
        'horizon.app.core.openstack-service-api.settings': settings,
        'horizon.app.core.images.imageFormats': imageFormats
      });
    }

    it('should call glance API on init', function() {
      var ctrl = createController();

      expect(glanceAPI.getImages).toHaveBeenCalledWith({paginate: false});
      expect(ctrl.kernelImages).toEqual([{disk_format: 'aki'}]);
      expect(ctrl.ramdiskImages).toEqual([{disk_format: 'ari'}]);
    });

    it('should have options for visibility, protected and copying', function() {
      var ctrl = createController();

      expect(ctrl.imageVisibilityOptions.length).toEqual(4);
      expect(ctrl.imageProtectedOptions.length).toEqual(2);
      expect(ctrl.imageCopyOptions.length).toEqual(2);
    });

    it("should destroy the image changed watcher when the controller is destroyed", function() {
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

    it("should set the default values", function() {
      var ctrl = createController();

      expect(ctrl.imageFormats).toBeDefined();
      expect(ctrl.validationRules).toBeDefined();
      expect(ctrl.diskFormats).toEqual([]);
      expect(ctrl.image.visibility).toEqual('shared');
      expect(ctrl.image.min_disk).toEqual(0);
      expect(ctrl.image.min_ram).toEqual(0);
    });

    describe('setFormats', function() {
      var ctrl;
      beforeEach(function() {
        ctrl = createController();
      });

      it('assumes bare container format', function() {
        ctrl.image_format = 'unknown';
        ctrl.setFormats();
        expect(ctrl.image.container_format).toBe('bare');
      });

      it('uses the given image format', function() {
        ctrl.image_format = 'unknown';
        ctrl.setFormats();
        expect(ctrl.image.disk_format).toBe('unknown');
      });

      it('sets container to ami/aki/ari if format is ami/aki/ari', function() {
        ['ami', 'aki', 'ari'].forEach(function(format) {
          ctrl.image_format = format;
          ctrl.setFormats();
          expect(ctrl.image.disk_format).toBe(format);
          expect(ctrl.image.container_format).toBe(format);
        });
      });

      it('sets docker/raw for container/disk if type is docker', function() {
        ctrl.image_format = 'docker';
        ctrl.setFormats();
        expect(ctrl.image.disk_format).toBe('raw');
        expect(ctrl.image.container_format).toBe('docker');
      });
    });

    describe('getConfiguredFormatsAndModes', function() {

      it('uses the settings for the source of allowed image formats', function() {
        var ctrl = createController();
        settingsCall.resolve({OPENSTACK_IMAGE_FORMATS: ['a', 'b', 'c']});
        $timeout.flush();
        var expectation = {
          'a': 'apple',
          'b': 'banana',
          'c': 'cherry'
        };
        expect(ctrl.imageFormats).toEqual(expectation);
      });

      describe('upload mode', function() {
        var urlSourceOption = { label: gettext('URL'), value: 'url' };

        it('set to "off" disables local file upload', function() {
          var ctrl = createController();
          settingsCall.resolve({
            OPENSTACK_IMAGE_FORMATS: [],
            HORIZON_IMAGES_UPLOAD_MODE: 'off',
            IMAGES_ALLOW_LOCATION: true
          });
          $timeout.flush();
          expect(ctrl.imageSourceOptions).toEqual([urlSourceOption]);
        });

        it('set to "off" and location disallowed disables all source options', function() {
          var ctrl = createController();
          settingsCall.resolve({
            OPENSTACK_IMAGE_FORMATS: [],
            HORIZON_IMAGES_UPLOAD_MODE: 'off',
            IMAGES_ALLOW_LOCATION: false
          });
          $timeout.flush();
          expect(ctrl.imageSourceOptions).toEqual([]);
        });

        it('set to a non-"off" value enables local file upload', function() {
          var ctrl = createController();
          var fileSourceOption = { label: gettext('File'), value: 'file-sample' };
          settingsCall.resolve({
            OPENSTACK_IMAGE_FORMATS: [],
            HORIZON_IMAGES_UPLOAD_MODE: 'sample',
            IMAGES_ALLOW_LOCATION: true
          });
          $timeout.flush();
          expect(ctrl.imageSourceOptions).toEqual([fileSourceOption, urlSourceOption]);
        });

        it('test image visibility is private if set as default', function() {
          var ctrl = createController();
          settingsCall.resolve({
            OPENSTACK_IMAGE_FORMATS: [],
            CREATE_IMAGE_DEFAULTS: { image_visibility: 'private' }
          });
          $timeout.flush();
          expect(ctrl.image.visibility).toEqual('private');
        });
      });
    });

    describe('isLocalFileUpload()', function() {
      var ctrl;

      beforeEach(function() {
        ctrl = createController();
      });

      it('returns true for source-type == "file-direct"', function() {
        ctrl.image = {source_type: 'file-direct'};
        expect(ctrl.isLocalFileUpload()).toBe(true);
      });

      it('returns true for source-type == "file-legacy"', function() {
        ctrl.image = {source_type: 'file-legacy'};
        expect(ctrl.isLocalFileUpload()).toBe(true);
      });

      it('returns false for any else source-type', function() {
        ctrl.image = {source_type: 'url'};
        expect(ctrl.isLocalFileUpload()).toBe(false);
      });

    });

  });
})();
