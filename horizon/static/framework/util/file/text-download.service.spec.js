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

  describe('textDownloadService', function() {
    var $scope, textDownload;

    beforeEach(module('horizon.framework.util.file'));
    beforeEach(inject(function($injector) {
      textDownload = $injector.get('horizon.framework.util.file.text-download');
      $scope = $injector.get('$rootScope');
    }));

    it('should return promise and it resolve filename after starting download file', function() {
      var promise = textDownload.downloadTextFile('content', 'download_file_name.txt');
      $scope.$apply();
      promise.then(function(contents) {
        expect(contents).toEqual('download_file_name.txt');
      });
    });
  });
})();
