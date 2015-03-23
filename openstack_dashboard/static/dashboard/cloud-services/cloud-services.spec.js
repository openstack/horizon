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

  describe('hz.dashboard', function () {

    //
    // factory:cloudServices
    //

    describe('factory:cloudServices', function () {
      var cloudServices;

      beforeEach(module('hz.dashboard', function ($provide) {
        $provide.value('cinderAPI', {});
        $provide.value('glanceAPI', {});
        $provide.value('keystoneAPI', {});
        $provide.value('neutronAPI', {});
        $provide.value('novaAPI', {});
        $provide.value('novaExtensions', {});
        $provide.value('securityGroup', {});
        $provide.value('serviceCatalog', {});
      }));

      beforeEach(inject(function ($injector) {
        cloudServices = $injector.get('cloudServices');
      }));

      it('should have `cloudServices` defined.', function () {
        expect(cloudServices).toBeDefined();
      });

      it('should have `cloudServices.cinder` defined.', function () {
        expect(cloudServices.cinder).toBeDefined();
      });

      it('should have `cloudServices.glance` defined.', function () {
        expect(cloudServices.glance).toBeDefined();
      });

      it('should have `cloudServices.keystone` defined.', function () {
        expect(cloudServices.keystone).toBeDefined();
      });

      it('should have `cloudServices.neutron` defined.', function () {
        expect(cloudServices.neutron).toBeDefined();
      });

      it('should have `cloudServices.nova` defined.', function () {
        expect(cloudServices.nova).toBeDefined();
      });

      it('should have `cloudServices.novaExtensions` defined.', function () {
        expect(cloudServices.novaExtensions).toBeDefined();
      });

    });

    //
    // factory:ifExtensionsEnabled
    //

    describe('factory:ifExtensionsEnabled', function () {
      var ifExtensionsEnabled,
          $q,
          cloudServices;

      beforeEach(module('hz.dashboard', function ($provide) {
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
        $provide.value('cloudServices', cloudServices);
      }));

      beforeEach(inject(function ($injector) {
        ifExtensionsEnabled = $injector.get('ifExtensionsEnabled');
      }));

      it('should have `ifExtensionsEnabled` defined as a function.', function () {
        expect(ifExtensionsEnabled).toBeDefined();
        expect(angular.isFunction(ifExtensionsEnabled)).toBe(true);
      });

      it('should call $q.all() and someService.ifEnabled() when invoking ifExtensionsEnabled().', function () {
        var extensions = ['ext1', 'ext2'];
        ifExtensionsEnabled('someService', extensions);
        expect($q.all).toHaveBeenCalled();
        expect(cloudServices.someService.ifEnabled).toHaveBeenCalled();
      });

      it('should not throw when passing in an empty extensions list.', function () {
        expect(function () {
          ifExtensionsEnabled('someService', []);
        }).not.toThrow();
      });

      it('should throw when extensions is null or undefined or not an array', function () {
        expect(function () {
          ifExtensionsEnabled('someService', null);
        }).toThrow();

        expect(function () {
          ifExtensionsEnabled('someService');
        }).toThrow();

        expect(function () {
          ifExtensionsEnabled('123');
        }).toThrow();
      });

      it('should not throw when the provided serviceName is not a key in the services hash table', function () {
        expect(function () {
          ifExtensionsEnabled('invlidServiceName', []);
        }).not.toThrow();
      });
    });

    //
    // factory:createDirectiveSpec
    //

    describe('factory:createDirectiveSpec', function () {
      var createDirectiveSpec,
          ifExtensionsEnabled;

      beforeEach(module('hz.dashboard', function ($provide) {
        ifExtensionsEnabled = function () {
          return {
            then: function (successCallback, errorCallback) {
            }
          };
        };
        $provide.value('ifExtensionsEnabled', ifExtensionsEnabled);
      }));

      beforeEach(inject(function ($injector) {
        createDirectiveSpec = $injector.get('createDirectiveSpec');
      }));

      it('should have `createDirectiveSpec` defined as a function.', function () {
        expect(createDirectiveSpec).toBeDefined();
        expect(angular.isFunction(createDirectiveSpec)).toBe(true);
      });

      describe('When called, the returned object', function () {
        var directiveSpec;

        beforeEach(function () {
          directiveSpec = createDirectiveSpec('someService');
        });

        it('should be defined.', function () {
          expect(directiveSpec).toBeDefined();
        });

        it('should have "restrict" property "E".', function () {
          expect(directiveSpec.restrict).toBe('E');
        });

        it('should have "transclude" property true.', function () {
          expect(directiveSpec.transclude).toBe(true);
        });

        it('should have "link" property as a function.', function () {
          expect(directiveSpec.link).toEqual(jasmine.any(Function));
        });

      });

    });

    //
    // directive:novaExtension
    //

    describe('directive:novaExtension', function () {
      var $timeout,
          $scope,
          html = [
            '<nova-extension required-extensions=\'["config_drive"]\'>',
              '<div class="child-element">',
              '</div>',
            '</nova-extension>'
          ].join(''),
          element;

      beforeEach(module('hz.dashboard', function ($provide) {
        $provide.value('ifExtensionsEnabled', function () {
          return {
            then: function (successCallback, errorCallback) {
              $timeout(successCallback);
            }
          };
        });
      }));

      beforeEach(inject(function ($injector) {
        var $compile = $injector.get('$compile');
        $scope = $injector.get('$rootScope').$new();
        $timeout = $injector.get('$timeout');
        element = $compile(html)($scope);
      }));

      it('should be compiled.', function () {
        expect(element.hasClass('ng-scope')).toBe(true);
      });

      it('should have class name `ng-hide` by default.', function () {
        expect(element.hasClass('ng-hide')).toBe(true);
      });

      it('should have no class name `ng-hide` after an asyncs callback.', function () {
        $timeout(function () {
          expect(element.hasClass('ng-hide')).toBe(false);
        });
        $timeout.flush();
      });

      it('should have the right child element.', function () {
        expect(element.children().first().hasClass('child-element')).toBe(true);
      });

    });

  })

;})();
