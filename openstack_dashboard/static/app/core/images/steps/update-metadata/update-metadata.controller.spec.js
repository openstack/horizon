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
(function () {
  'use strict';

  describe('horizon.app.core.images', function () {

    describe('controller.UpdateMetadataController', function () {
      var mockTree = {
        getExisting: function() {}
      };

      var availableMetadata = {id: 'availableMetadata'};
      var existingMetadata = {id: 'existingMetadata'};

      var metadataService = {
        getNamespaces: function() {
          return {
            then: function(callback) {
              callback({
                data: {
                  items: availableMetadata
                }
              });
            }
          };
        },
        getMetadata: function() {
          return {
            then: function(callback) {
              callback({
                data: existingMetadata
              });
            }
          };
        }
      };

      var metadataTreeService = {
        Tree: function() {}
      };

      var $controller, $scope, $q;

      beforeEach(module('horizon.framework'));
      beforeEach(module('horizon.framework.widgets'));
      beforeEach(module('horizon.framework.widgets.metadata.tree'));
      beforeEach(module('horizon.app.core.images'));

      beforeEach(module(function($provide) {
        $provide.value('horizon.framework.widgets.metadata.tree.service', metadataTreeService);
        $provide.value('horizon.app.core.metadata.service', metadataService);
      }));

      beforeEach(inject(function($injector, _$rootScope_, _$q_) {
        $controller = $injector.get('$controller');
        $scope = _$rootScope_.$new();
        $q = _$q_;
      }));

      it('should setup up the metadata tree', function() {
        var deferred = $q.defer();
        deferred.resolve({data: {id: '1'}});
        $scope.imagePromise = deferred.promise;

        spyOn(metadataTreeService, 'Tree').and.returnValue(mockTree);
        spyOn(metadataService, 'getNamespaces').and.callThrough();
        spyOn(metadataService, 'getMetadata').and.callThrough();

        var ctrl = createController();
        $scope.$apply();

        expect(ctrl.tree).toEqual(mockTree);
        expect(metadataTreeService.Tree).toHaveBeenCalledWith([], []);
        expect(metadataTreeService.Tree).toHaveBeenCalledWith(availableMetadata, existingMetadata);
      });

      it('should setup up the metadata tree even without an image', function() {
        expect($scope.imagePromise).toBeUndefined();

        spyOn(metadataTreeService, 'Tree').and.returnValue(mockTree);
        spyOn(metadataService, 'getNamespaces').and.callThrough();
        spyOn(metadataService, 'getMetadata').and.callThrough();

        var ctrl = createController();
        $scope.$apply();

        expect(ctrl.tree).toEqual(mockTree);
        expect(metadataTreeService.Tree).toHaveBeenCalledWith(availableMetadata, []);
      });

      it('should setup up the metadata tree if image does not exist', function() {
        var deferred = $q.defer();
        deferred.resolve({data: {}});
        $scope.imagePromise = deferred.promise;

        spyOn(metadataTreeService, 'Tree').and.returnValue(mockTree);
        spyOn(metadataService, 'getNamespaces').and.callThrough();

        var ctrl = createController();
        $scope.$apply();

        expect(ctrl.tree).toEqual(mockTree);
        expect(metadataTreeService.Tree).toHaveBeenCalledWith([], []);
        expect(metadataTreeService.Tree).toHaveBeenCalledWith(availableMetadata, []);
      });

      it('should emit imageMetadataChanged event when metadata changes', function() {
        var deferred = $q.defer();
        deferred.resolve({data: {id: '1'}});
        $scope.imagePromise = deferred.promise;
        spyOn(metadataTreeService, 'Tree').and.returnValue(mockTree);

        createController();

        spyOn($scope, '$emit').and.callThrough();
        var mockGetExisting = spyOn(mockTree, 'getExisting');

        mockGetExisting.and.returnValue('1');
        $scope.$apply();

        mockGetExisting.and.returnValue('2');
        $scope.$apply();

        expect($scope.$emit).toHaveBeenCalledWith(
          'horizon.app.core.images.IMAGE_METADATA_CHANGED',
          '2'
        );
      });

      function createController() {
        return $controller('horizon.app.core.images.steps.UpdateMetadataController', {
          '$scope': $scope,
          'metadataService': metadataService,
          'metadataTreeService': metadataTreeService
        });
      }

    });
  });
})();
