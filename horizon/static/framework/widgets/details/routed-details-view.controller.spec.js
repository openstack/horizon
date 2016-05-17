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

  describe('RoutedDetailsViewController', function() {
    var ctrl, deferred, $timeout;

    beforeEach(module('horizon.framework.widgets.details'));
    beforeEach(inject(function($injector, $controller, $q, _$timeout_) {
      deferred = $q.defer();
      $timeout = _$timeout_;

      var service = {
        getResourceType: function() { return {
          load: function() { return deferred.promise; },
          parsePath: function() { return {a: 'my-context'}; },
          itemName: function() { return 'A name'; }
        }; },
        getDefaultDetailsTemplateUrl: angular.noop,
        initActions: angular.noop
      };

      ctrl = $controller("RoutedDetailsViewController", {
        'horizon.framework.conf.resource-type-registry.service': service,
        '$routeParams': {
          type: 'OS::Glance::Image',
          path: '1234'
        }
      });
    }));

    it('sets resourceType', function() {
      expect(ctrl.resourceType).toBeDefined();
    });

    it('sets context', function() {
      expect(ctrl.context.a).toEqual('my-context');
    });

    it('sets itemData when item loads', function() {
      deferred.resolve({data: {some: 'data'}});
      expect(ctrl.itemData).toBeUndefined();
      $timeout.flush();
      expect(ctrl.itemData).toEqual({some: 'data'});
    });

    it('sets itemName when item loads', function() {
      deferred.resolve({data: {some: 'data'}});
      expect(ctrl.itemData).toBeUndefined();
      $timeout.flush();
      expect(ctrl.itemName).toEqual('A name');
    });
  });

})();
