/*
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

  describe('horizon.framework.util.promise-toggle', function () {

    describe('directive:hz-promise-toggle-mock', function () {
      var $compile, $q, $scope, mockService, baseElement;

      var $mockHtmlInput = '$mock-input';
      var baseHtml = [
        '<div>',
        '<div hz-promise-toggle-mock=\'$mock-input\'>',
        '<div class="child-element">',
        '</div>',
        '</div>',
        '</div>'
      ].join('');

      beforeEach(function() {
        mockService = {
          mockResolver: function(shouldResolve) {
            var deferred = $q.defer();

            if (shouldResolve === 'true') {
              deferred.resolve();
            } else {
              deferred.reject();
            }

            return deferred.promise;
          }
        };

        spyOn(mockService, 'mockResolver').and.callThrough();

        module('horizon.framework.util.promise-toggle', function ($provide) {
          $provide.value('mockService', mockService);
        });

        inject(function (_$compile_, _$q_, _$rootScope_) {
          $compile = _$compile_;
          $q = _$q_;
          $scope = _$rootScope_.$new();
          baseElement = null;
        });

      });

      it('should evaluate the given attribute name', function () {
        $scope.test = {
          retVal: 'true'
        };

        var params = 'test.retVal';

        var template = baseHtml.replace($mockHtmlInput, params);

        baseElement = $compile(template)($scope);

        shouldHaveCompiledContent(true);

        expect(mockService.mockResolver).toHaveBeenCalledWith('true');
      });

      it('should be compiled for one resolved promise', function () {
        var params = '\"true\"';
        var template = baseHtml.replace($mockHtmlInput, params);

        baseElement = $compile(template)($scope);

        shouldHaveCompiledContent(true);

        expect(mockService.mockResolver).toHaveBeenCalledWith('true');
      });

      it('should be compiled for multiple resolved promises', function () {
        var params = '[\"true\", \"true\"]';
        var template = baseHtml.replace($mockHtmlInput, params);

        baseElement = $compile(template)($scope);

        shouldHaveCompiledContent(true);

        expect(mockService.mockResolver).toHaveBeenCalledWith('true');
        expect(mockService.mockResolver.calls.count()).toEqual(2);
      });

      it('should not be compiled for one rejected promise', function () {
        var params = '\"false\"';
        var template = baseHtml.replace($mockHtmlInput, params);

        baseElement = $compile(template)($scope);

        shouldHaveCompiledContent(false);

        expect(mockService.mockResolver).toHaveBeenCalledWith('false');
      });

      it('should not be compiled for mixed resolved & rejected promise', function () {
        var params = '[\"true\", \"false\", \"true\"]';
        var template = baseHtml.replace($mockHtmlInput, params);

        baseElement = $compile(template)($scope);

        shouldHaveCompiledContent(false);

        expect(mockService.mockResolver).toHaveBeenCalledWith('true');
        expect(mockService.mockResolver).toHaveBeenCalledWith('false');
        expect(mockService.mockResolver.calls.count()).toEqual(3);
      });

      function shouldHaveCompiledContent(shouldInclude) {
        $scope.$apply();

        var baseElementChildren = baseElement.children();

        if (shouldInclude) {
          var includedContent = baseElementChildren.first();
          expect(includedContent.hasClass('ng-scope')).toBe(true);
          expect(includedContent.children().first().hasClass('child-element')).toBe(true);
        } else {
          expect(baseElementChildren.length).toBe(0);
        }
      }

    });
  });

})();
