/*
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function() {
  'use strict';

  describe('load-edit directive', function () {
    var $compile,
      $scope,
      key,
      element,
      $q,
      readFileService;

    beforeEach(module('templates'));
    beforeEach(module('horizon.framework.widgets.load-edit'));
    beforeEach(module(function($provide) {
      readFileService = {};
      $provide.provider('horizon.framework.util.file.file-reader',
        function () {
          this.$get = function () {
            return readFileService;
          };
        });
    }));
    beforeEach(inject(function ($injector) {
      $scope = $injector.get('$rootScope').$new();
      $q = $injector.get('$q');
      $compile = $injector.get('$compile');
      key = 'elementKey';
      element = $compile(
        '<load-edit title="{}" model="{}" max-bytes="{}" key="' + key + '" ' +
        'required="true" rows="8"></load-edit>'
      )($scope);
      $scope.$apply();
    }));

    describe('onTextAreaChange listener', function() {
      var textarea;

      beforeEach(function() {
        textarea = element.find('textarea');
      });

      it('should set textModified to true when textarea has content', function () {
        textarea.val('any value');
        textarea.trigger('propertychange');
        $scope.$apply();

        expect(element.isolateScope().textModified).toBe(true);
      });

      it('should set textModified to false when textarea has no content', function () {
        textarea.val('');
        textarea.trigger('propertychange');
        $scope.$apply();

        expect(element.isolateScope().textModified).toBe(false);
      });

      it('should set userInput to the value of the textarea', function() {
        textarea.val('user input');
        textarea.trigger('input');
        $scope.$apply();

        expect(element.isolateScope().model).toBe('user input');
      });
    });

    describe('onFileLoadListener', function() {
      it('should set the value of textContent to the file contents', function(done) {
        var contentPromise = $q.defer();
        readFileService.readTextFile = function() {
          return contentPromise.promise;
        };

        var fileInput = element.find('input[type="file"]');
        var e = jQuery.Event("change", {originalEvent: {target: {files: [['hi']]}}});
        fileInput.trigger(e);

        contentPromise.promise.then(function() {
          expect(element.isolateScope().textContent).toBe('the contents of a file');
          done();
        });
        contentPromise.resolve('the contents of a file');
        $scope.$apply();
      });

      it('should handle when no file is passed in', function() {
        var fileInput = element.find('input[type="file"]');
        var e = jQuery.Event("change", {originalEvent: {target: {files: []}}});

        fileInput.trigger(e);

        expect(element.isolateScope().textContent).toBe('');
      });
    });
  });
})();
