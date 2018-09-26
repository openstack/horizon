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
    var ctrl, deferred, $timeout, $q, service, redirect, actionResultService, navigationsService;

    beforeEach(module('horizon.framework.widgets.details'));
    beforeEach(inject(function($injector, $controller, _$q_, _$timeout_) {
      $q = _$q_;
      deferred = $q.defer();
      $timeout = _$timeout_;

      service = {
        resourceTypes: {'OS::Glance::Image': {}},
        getResourceType: function() {
          return {
            load: function() { return deferred.promise; },
            parsePath: function() { return 'my-context'; },
            itemName: function() { return 'A name'; },
            initActions: angular.noop,
            getDefaultIndexUrl: function() { return '/project/images/'; }
          };
        },
        getDefaultDetailsTemplateUrl: angular.noop
      };

      redirect = {
        responseError: angular.noop,
        notFound: angular.noop
      };

      actionResultService = {
        getIdsOfType: function() { return []; }
      };

      navigationsService = {
        expandNavigationByUrl: function() { return ['Project', 'Compute', 'Images']; },
        setBreadcrumb: angular.noop,
        getActivePanelUrl: function() { return 'project/fancypanel'; },
        nav: true,
        isNavigationExists: function() { return navigationsService.nav; }
      };

      ctrl = $controller("RoutedDetailsViewController", {
        'horizon.framework.conf.resource-type-registry.service': service,
        'horizon.framework.redirect': redirect,
        'horizon.framework.util.actions.action-result.service': actionResultService,
        'horizon.framework.util.navigations.service': navigationsService,
        'horizon.framework.widgets.modal-wait-spinner.service': {
          showModalSpinner: angular.noop,
          hideModalSpinner: angular.noop
        },
        '$routeParams': {
          type: 'OS::Glance::Image',
          path: '1234'
        }
      });
      spyOn(redirect, 'notFound');
    }));

    describe('RoutedDetailsViewController', function() {
      beforeEach(inject(function($controller) {
        service.resourceTypes = {};
        ctrl = $controller("RoutedDetailsViewController", {
          'horizon.framework.conf.resource-type-registry.service': service,
          'horizon.framework.redirect': redirect,
          'horizon.framework.util.actions.action-result.service': actionResultService,
          'horizon.framework.util.navigations.service': navigationsService,
          'horizon.framework.widgets.modal-wait-spinner.service': {
            showModalSpinner: angular.noop,
            hideModalSpinner: angular.noop
          },
          '$routeParams': {
            type: 'not exist',
            path: 'xxxx'
          }
        });
      }));

      it('call redirect.notFound when resource type is not registered', function() {
        expect(redirect.notFound).toHaveBeenCalled();
      });
    });

    it('sets resourceType', function() {
      expect(ctrl.resourceType).toBeDefined();
    });

    it('sets context', function() {
      expect(ctrl.context.identifier).toEqual('my-context');
    });

    it('sets itemData when item loads', function() {
      deferred.resolve({data: {some: 'data'}});
      expect(ctrl.itemData).toBeUndefined();
      $timeout.flush();
      expect(ctrl.itemData).toEqual({some: 'data'});
    });

    it('call redirect.notFound when item not found', function() {
      deferred.reject({status: 404});
      $timeout.flush();
      expect(redirect.notFound).toHaveBeenCalled();
    });

    it('does not call redirect.notFound when server error occurred', function() {
      deferred.reject({status: 500});
      $timeout.flush();
      expect(redirect.notFound).not.toHaveBeenCalled();
    });

    it('sets itemName when item loads', function() {
      deferred.resolve({data: {some: 'data'}});
      expect(ctrl.itemData).toBeUndefined();
      $timeout.flush();
      expect(ctrl.itemName).toEqual('A name');
    });

    describe('resultHandler', function() {

      it('handles empty results', function() {
        var result = $q.defer();
        result.resolve({});
        ctrl.resultHandler(result.promise);
        $timeout.flush();
        expect(ctrl.showDetails).not.toBe(true);
      });

      it('handles falsy results', function() {
        var result = $q.defer();
        result.resolve(false);
        ctrl.resultHandler(result.promise);
        $timeout.flush();
        expect(ctrl.showDetails).not.toBe(true);
      });

      it('handles matched results', function() {
        spyOn(actionResultService, 'getIdsOfType').and.returnValue([1, 2, 3]);
        var result = $q.defer();
        result.resolve({some: 'thing'});
        ctrl.resultHandler(result.promise);
        deferred.resolve({data: {some: 'data'}});
        $timeout.flush();
        expect(ctrl.showDetails).toBe(true);
      });

      it('handles deleted results and redirect back to index view', function() {
        spyOn(actionResultService, 'getIdsOfType').and.returnValue([1, 2, 3]);
        spyOn(navigationsService, 'getActivePanelUrl');
        var result = $q.defer();
        result.resolve({created: [], updated: [], deleted: ['image1'], failed: []});
        ctrl.resultHandler(result.promise);
        $timeout.flush();
        expect(ctrl.showDetails).toBe(false);
        expect(navigationsService.getActivePanelUrl).toHaveBeenCalled();
      });

      it('handles general results and do not redirect back to index view', function() {
        spyOn(navigationsService, 'getActivePanelUrl');
        var result = $q.defer();
        result.resolve({created: [], updated: ['image1'], deleted: [], failed: []});
        ctrl.resultHandler(result.promise);
        $timeout.flush();
        expect(ctrl.showDetails).toBe(false);
        expect(navigationsService.getActivePanelUrl).not.toHaveBeenCalled();
      });

    });
  });

})();
