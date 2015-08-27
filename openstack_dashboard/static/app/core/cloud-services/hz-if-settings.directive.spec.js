/*
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

(function () {
  'use strict';

  describe('horizon.app.core.cloud-services.hzIfSettings', function () {
    var $compile, $scope, deferred, settingsServiceAPI;

    var template = [
      '<div>',
      '<div hz-if-settings=\'\"setting_name\"\'>',
      '<div class="child-element">',
      '</div>',
      '</div>',
      '</div>'
    ].join('');

    beforeEach(function() {
      settingsServiceAPI = {
        ifEnabled: function() {
          return deferred.promise;
        }
      };

      spyOn(settingsServiceAPI, 'ifEnabled').and.callThrough();

      module('horizon.app.core.cloud-services');
      module('horizon.framework.util.promise-toggle');

      module('horizon.app.core.openstack-service-api', function($provide) {
        $provide.value(
          'horizon.app.core.openstack-service-api.settings', settingsServiceAPI
        );
      });

      inject(function (_$compile_, _$q_, _$rootScope_) {
        $compile = _$compile_;
        deferred = _$q_.defer();
        $scope = _$rootScope_.$new();
      });

    });

    // Please note, this code is primarily intended to verify that the
    // directive specifies the correct name and that it uses the settings
    // service API. Testing of the variations on inputs being resolved
    // are tested in the hz-promise-toggle spec.
    it('should evaluate child elements when setting is enabled', function () {
      var element = $compile(template)($scope);

      deferred.resolve();

      expect(element.children().length).toBe(0);
      expect(settingsServiceAPI.ifEnabled).toHaveBeenCalledWith('setting_name');

      $scope.$apply();
      expect(element.children().length).toBe(1);
    });

    it('should not evaluate child elements when setting is disabled', function () {
      var element = $compile(template)($scope);

      deferred.reject();

      expect(element.children().length).toBe(0);
      expect(settingsServiceAPI.ifEnabled).toHaveBeenCalledWith('setting_name');

      $scope.$apply();
      expect(element.children().length).toBe(0);
    });

  });

})();
