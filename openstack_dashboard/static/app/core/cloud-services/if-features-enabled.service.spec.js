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

  describe('horizon.app.core.cloud-services', function () {

    describe('factory:ifFeaturesEnabled', function () {
      var ifFeaturesEnabled,
          $q,
          cloudServices;

      beforeEach(module('horizon.app.core.cloud-services', function ($provide) {
        $q = {
          all: function () {
            return {
              then: function () {}
            };
          }
        };

        cloudServices = {
          'someService': {
            ifEnabled: function () {}
          }
        };

        spyOn(cloudServices.someService, 'ifEnabled');
        spyOn($q, 'all');

        $provide.value('$q', $q);
        $provide.value('horizon.app.core.cloud-services.cloudServices', cloudServices);
      }));

      beforeEach(inject(function ($injector) {
        ifFeaturesEnabled = $injector.get('horizon.app.core.cloud-services.ifFeaturesEnabled');
      }));

      it('should have `ifFeaturesEnabled` defined as a function', function () {
        expect(ifFeaturesEnabled).toBeDefined();
        expect(angular.isFunction(ifFeaturesEnabled)).toBe(true);
      });

      it('should call $q.all() and someService.ifEnabled() when invoking ifFeaturesEnabled()',
        function () {
          var extensions = ['ext1', 'ext2'];
          ifFeaturesEnabled('someService', extensions);
          expect($q.all).toHaveBeenCalled();
          expect(cloudServices.someService.ifEnabled).toHaveBeenCalled();
        }
      );

      it('should not throw when passing in an empty extensions list', function () {
        expect(function () {
          ifFeaturesEnabled('someService', []);
        }).not.toThrow();
      });

      it('should throw when extensions is null or undefined or not an array', function () {
        expect(function () {
          ifFeaturesEnabled('someService', null);
        }).toThrow();

        expect(function () {
          ifFeaturesEnabled('someService');
        }).toThrow();

        expect(function () {
          ifFeaturesEnabled('123');
        }).toThrow();
      });

      it('should not throw when the provided serviceName is not a key in the services hash table',
        function () {
          expect(function () {
            ifFeaturesEnabled('invlidServiceName', []);
          }).not.toThrow();
        }
      );
    });
  });

})();
