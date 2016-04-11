/**
 * Copyright 2015 IBM Corp.
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

  describe('horizon.dashboard.identity', function() {
    it('should exist', function() {
      expect(angular.module('horizon.dashboard.identity')).toBeDefined();
    });
  });

  describe('horizon.dashboard.identity.basePath constant', function() {
    var identityBasePath, staticUrl;

    beforeEach(module('horizon.dashboard.identity'));
    beforeEach(inject(function($injector) {
      identityBasePath = $injector.get('horizon.dashboard.identity.basePath');
      staticUrl = $injector.get('$window').STATIC_URL;
    }));

    it('should equal to "/static/dashboard/identity/"', function() {
      expect(identityBasePath).toEqual(staticUrl + 'dashboard/identity/');
    });
  });

})();
