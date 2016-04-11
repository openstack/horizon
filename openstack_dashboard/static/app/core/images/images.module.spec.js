/**
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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
(function () {
  'use strict';

  describe('horizon.app.core.images', function () {
    it('should exist', function () {
      expect(angular.module('horizon.app.core.images')).toBeDefined();
    });
  });

  describe('horizon.app.core.images.tableRoute constant', function () {
    var tableRoute;

    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.images'));
    beforeEach(inject(function ($injector) {
      tableRoute = $injector.get('horizon.app.core.images.tableRoute');
    }));

    it('should be defined', function () {
      expect(tableRoute).toBeDefined();
    });

    it('should equal to "project/ngimages/"', function () {
      expect(tableRoute).toEqual('project/ngimages/');
    });
  });

  describe('horizon.app.core.images.detailsRoute constant', function () {
    var detailsRoute;

    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.images'));
    beforeEach(inject(function ($injector) {
      detailsRoute = $injector.get('horizon.app.core.images.detailsRoute');
    }));

    it('should be defined', function () {
      expect(detailsRoute).toBeDefined();
    });

    it('should equal to "project/ngimages/details/"', function () {
      expect(detailsRoute).toEqual('project/ngimages/details/');
    });
  });

  describe('$routeProvider should be configured for images', function() {
    var staticUrl, $routeProvider;

    beforeEach(function() {
      module('ngRoute');
      angular.module('routeProviderConfig', [])
        .config(function(_$routeProvider_) {
          $routeProvider = _$routeProvider_;
          spyOn($routeProvider, 'when').and.callThrough();
        });

      module('routeProviderConfig');
      module('horizon.app.core');

      inject(function ($injector) {
        staticUrl = $injector.get('$window').STATIC_URL;
      });
    });

    it('should set table and detail path', function() {
      expect($routeProvider.when.calls.count()).toEqual(2);
      var imagesRouteCallArgs = $routeProvider.when.calls.argsFor(0);
      expect(imagesRouteCallArgs).toEqual([
        '/project/ngimages/', {templateUrl: staticUrl + 'app/core/images/table/images-table.html'}
      ]);
      var imagesDetailsCallArgs = $routeProvider.when.calls.argsFor(1);
      expect(imagesDetailsCallArgs).toEqual([
        '/project/ngimages/details/:imageId',
        { templateUrl: staticUrl + 'app/core/images/detail/image-detail.html'}
      ]);
    });

  });

})();
