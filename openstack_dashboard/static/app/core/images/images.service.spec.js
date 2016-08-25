/*
 * (c) Copyright 2016 Hewlett Packard Enterprise Development LP
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
  "use strict";

  describe('images service', function() {
    var service;
    beforeEach(module('horizon.app.core.images'));
    beforeEach(inject(function($injector) {
      service = $injector.get('horizon.app.core.images.service');
    }));

    it("getDetailsPath creates urls using the item's ID", function() {
      var myItem = {id: "1234"};
      expect(service.getDetailsPath(myItem)).toBe('project/ngdetails/OS::Glance::Image/1234');
    });

    describe('imageType', function() {
      it("imageType returns Snapshot when appropriate", function() {
        var myItem = {properties: {image_type: 'snapshot'}};
        expect(service.imageType(myItem)).toBe('Snapshot');
      });

      it("imageType returns Image when no item", function() {
        var myItem;
        expect(service.imageType(myItem)).toBe('Image');
      });

      it("imageType returns Image when no properties", function() {
        var myItem = {};
        expect(service.imageType(myItem)).toBe('Image');
      });

      it("imageType returns Image when properties but not type 'snapshot'", function() {
        var myItem = {properties: {image_type: 'unknown'}};
        expect(service.imageType(myItem)).toBe('Image');
      });
    });

    describe('isInTransition Function', function() {
      it("should return true for known transitional statuses", function() {
        var statuses = ["saving", "queued", "pending_delete"];
        statuses.forEach(function(status) {
          var myItem = {status: status};
          expect(service.isInTransition(myItem)).toBe(true);
        });
      });

      it("should return false for unknown statuses", function() {
        var myItem = {status: "notATransitionalState"};
        expect(service.isInTransition(myItem)).toBe(false);
      });

      it("should return false for an empty status", function() {
        var myItem = {status: undefined};
        expect(service.isInTransition(myItem)).toBe(false);
      });

      it("should return false for an undefined status", function() {
        var myItem = {status: undefined};
        expect(service.isInTransition(myItem)).toBe(false);
      });

      it("should return false for a non-string status", function() {
        var statuses = [3, true, false];
        statuses.forEach(function(status) {
          var myItem = {status: status};
          expect(service.isInTransition(myItem)).toBe(false);
        });
      });
    });

    describe('getImagesPromise', function() {
      it("provides a promise that gets translated", inject(function($q, $injector, $timeout) {
        var glance = $injector.get('horizon.app.core.openstack-service-api.glance');
        var session = $injector.get('horizon.app.core.openstack-service-api.userSession');
        var deferred = $q.defer();
        var deferredSession = $q.defer();
        spyOn(glance, 'getImages').and.returnValue(deferred.promise);
        spyOn(session, 'get').and.returnValue(deferredSession.promise);
        var result = service.getImagesPromise({});
        deferred.resolve({data: {items: [{id: 1, updated_at: 'jul1'}]}});
        deferredSession.resolve({project_id: '12'});
        $timeout.flush();
        expect(result.$$state.value.data.items[0].trackBy).toBe('1jul1');
      }));
    });

    describe('getImagePromise', function() {
      it("provides a promise", inject(function($q, $injector) {
        var glance = $injector.get('horizon.app.core.openstack-service-api.glance');
        var deferred = $q.defer();
        spyOn(glance, 'getImage').and.returnValue(deferred.promise);
        var result = service.getImagePromise({});
        deferred.resolve({id: 1, updated_at: 'jul1'});
        expect(glance.getImage).toHaveBeenCalled();
        expect(result.$$state.value.updated_at).toBe('jul1');
      }));
    });
  });

})();
