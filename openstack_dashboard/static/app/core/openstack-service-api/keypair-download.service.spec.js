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

(function() {
  'use strict';

  describe('Download Keypair Service', function() {

    var service, $scope, existingKeypairs, $timeout;

    var documentMock = {
      find: function() {
        return documentFindMock;
      }
    };

    var documentFindMock = {
      append : angular.noop,
      load: function (callback) {
        callback();
      },
      size: function() {
        return 1;
      }
    };

    var novaAPIMock = {
      getKeypairs: function() {
        return {
          then: function(callback) {
            callback(existingKeypairs);
          }
        };
      },
      getCreateKeypairUrl: function() {
        return "/some/given/path";
      }
    };

    beforeEach(module('horizon.app.core.openstack-service-api'));

    beforeEach(module(function ($provide) {
      $provide.value('horizon.app.core.openstack-service-api.nova', novaAPIMock);
      $provide.value('$document', documentMock);
    }));

    beforeEach(inject(function (_$injector_, _$rootScope_, _$timeout_) {
      service = _$injector_.get(
        'horizon.app.core.openstack-service-api.keypair-download-service'
      );
      $scope = _$rootScope_.$new();
      $timeout = _$timeout_;
    }));

    it('adds the download key pair endpoint as a resource to the DOM', function() {
      spyOn(documentFindMock, 'append');
      spyOn(documentFindMock, 'load').and.returnValue({});

      service.createAndDownloadKeypair("newKeypair");

      var passedObj = documentFindMock.append.calls.argsFor(0)[0];
      expect(passedObj).toBeDefined();
      expect(passedObj.attr('id')).toBe("newKeypair");
    });

    it('encodes the URI component given slashes, etc.', function() {
      spyOn(documentFindMock, 'append');
      spyOn(documentFindMock, 'load').and.returnValue({});

      service.createAndDownloadKeypair("new/Keypair");

      var passedObj = documentFindMock.append.calls.argsFor(0)[0];
      expect(passedObj).toBeDefined();
      expect(passedObj.attr('id')).toBe("new/Keypair");
    });

    it('creates a div with download-iframes if not present', function() {
      spyOn(documentFindMock, 'append');
      spyOn(documentFindMock, 'load').and.returnValue({});
      spyOn(documentFindMock, 'size').and.returnValue(0);

      service.createAndDownloadKeypair("new/Keypair");

      expect(documentFindMock.append.calls.count()).toBe(2);
      expect(documentFindMock.append.calls.allArgs().some(function(x) {
        return x[0].attr('class') === 'download-iframes';
      })).toBe(true);
    });

    it('checks that the keypair was added and returns a success promise result', function() {

      existingKeypairs = {
        data: {
          items:[{
            keypair: {
              name: "newKeypair"
            }
          }]
        }
      };

      var promiseSuccessful, keypair;

      service.createAndDownloadKeypair("newKeypair").then(
        function success(createdKeypair) {
          promiseSuccessful = true;
          keypair = createdKeypair;
        }
      );

      $timeout.flush();
      $scope.$apply();

      expect(promiseSuccessful).toEqual(true);
      expect(keypair).toEqual({name: "newKeypair"});
    });

    it('checks that the keypair was not added and returns a error promise result', function() {

      existingKeypairs = {
        data: {
          items:[]
        }
      };

      var promiseErrored;

      service.createAndDownloadKeypair("newKeypair").then(
        function success() {},
        function error() {
          promiseErrored = true;
        }
      );

      // checks 10 times after one second
      $timeout.flush();
      $timeout.flush();
      $timeout.flush();
      $timeout.flush();
      $timeout.flush();
      $timeout.flush();
      $timeout.flush();
      $timeout.flush();
      $timeout.flush();
      $timeout.flush();

      $scope.$apply();

      expect(promiseErrored).toEqual(true);
    });

  });
})();
