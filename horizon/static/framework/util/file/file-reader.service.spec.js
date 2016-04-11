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

  describe('fileReader service', function() {
    var $scope, fileReader;

    beforeEach(module('horizon.framework.util.file'));
    beforeEach(inject(function($injector) {
      fileReader = $injector.get('horizon.framework.util.file.file-reader');
      $scope = $injector.get('$rootScope');
    }));

    it('should return a promise that resolves to a string', function(done) {
      var fileReaderStub = {};
      var arrayBuffer = str2ab('file contents');
      fileReaderStub.readAsArrayBuffer = function() {};

      var filePromise = fileReader.readTextFile('file', fileReaderStub);
      filePromise.then(function(contents) {
        expect(contents).toEqual('file contents');
        done();
      });

      fileReaderStub.onloadend({
        target: {
          result: arrayBuffer
        }
      });
      $scope.$apply();
    });
  });

  function str2ab(str) {
    var buf = new ArrayBuffer(str.length); // 2 bytes for each char
    var bufView = new Uint8Array(buf);
    for (var i = 0, strLen = str.length; i < strLen; i++) {
      bufView[i] = str.charCodeAt(i);
    }
    return buf;
  }
})();
