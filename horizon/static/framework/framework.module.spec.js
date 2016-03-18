/**
 * Copyright 2015 ThoughtWorks Inc.
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

  describe('horizon.framework', function() {
    // Mock $window. This allows our mock $window to be used
    // by horizon.framework's config block instead of the
    // real $window service. This prevents accidentally redirecting
    // the browser during testing.
    beforeEach(module('horizon.framework', function($windowProvider) {
      var window = {
        location: {
          replace: jasmine.createSpy()
        }
      };

      $windowProvider.$get = function() {
        return window;
      };
    }));

    describe('when unauthorized', function() {
      it('should redirect to /auth/logout', inject(function($http, $httpBackend, $window) {
        $window.WEBROOT = '/dashboard/';
        $httpBackend.when('GET', '/api').respond(401, '');

        $http.get('/api').error(function() {
          expect($window.location.replace).toHaveBeenCalledWith('/dashboard/auth/logout');
        });
        $httpBackend.flush();
      }));
    });
  });
})();
