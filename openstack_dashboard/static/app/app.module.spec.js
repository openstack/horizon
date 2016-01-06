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
(function () {
  'use strict';

  describe('horizon.app', function () {
    it('should be defined', function () {
      expect(angular.module('horizon.app')).toBeDefined();
    });
  });

  describe('$locationProvider', function() {
    var $locationProvider;

    beforeEach(function() {
      angular.module('horizon.auth', []);
      angular.module('locationProviderConfig', [])
        .config(function(_$locationProvider_) {
          $locationProvider = _$locationProvider_;
          spyOn($locationProvider, 'html5Mode').and.callThrough();
          spyOn($locationProvider, 'hashPrefix').and.callThrough();
        });

      module('locationProviderConfig');
      module('horizon.app');

      inject();
    });

    it('should set html5 mode', function() {
      expect($locationProvider.html5Mode).toHaveBeenCalledWith(true);
    });

    it('should set hashPrefix', function() {
      expect($locationProvider.hashPrefix).toHaveBeenCalledWith('!');
    });

  });

})();
