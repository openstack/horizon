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

  describe('image overview controller', function() {
    var ctrl;
    var sessionObj = {project_id: '12'};
    var glance = {
      getNamespaces: angular.noop
    };

    beforeEach(module('horizon.app.core.images'));
    beforeEach(module('horizon.framework.conf'));
    beforeEach(inject(function($controller, $q, $injector) {
      var session = $injector.get('horizon.app.core.openstack-service-api.userSession');
      var deferred = $q.defer();
      var sessionDeferred = $q.defer();
      deferred.resolve({data: {properties: [{'a': 'apple'}, [], {}]}});
      sessionDeferred.resolve(sessionObj);
      spyOn(glance, 'getNamespaces').and.returnValue(deferred.promise);
      spyOn(session, 'get').and.returnValue(sessionDeferred.promise);
      ctrl = $controller('ImageOverviewController',
        {
          '$scope': {context: {loadPromise: deferred.promise}}
        }
      );
    }));

    it('sets ctrl.resourceType', function() {
      expect(ctrl.resourceType).toBeDefined();
    });

    it('sets ctrl.images.properties (metadata)', inject(function($timeout) {
      $timeout.flush();
      expect(ctrl.image).toBeDefined();
      expect(ctrl.image.properties).toBeDefined();
      expect(ctrl.image.properties[0].name).toEqual('0');
      expect(ctrl.image.properties[0].value).toEqual({'a': 'apple'});
    }));

    it('sets ctrl.images.properties propValue if empty array', inject(function($timeout) {
      $timeout.flush();
      expect(ctrl.image).toBeDefined();
      expect(ctrl.image.properties).toBeDefined();
      expect(ctrl.image.properties[1].name).toEqual('1');
      expect(ctrl.image.properties[1].value).toEqual('');
    }));

    it('sets ctrl.images.properties propValue if empty object', inject(function($timeout) {
      $timeout.flush();
      expect(ctrl.image).toBeDefined();
      expect(ctrl.image.properties).toBeDefined();
      expect(ctrl.image.properties[2].name).toEqual('2');
      expect(ctrl.image.properties[2].value).toEqual({});
    }));

    it('sets ctrl.projectId', inject(function($timeout) {
      $timeout.flush();
      expect(ctrl.projectId).toBe(sessionObj.project_id);
    }));

  });

})();
