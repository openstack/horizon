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

  angular
    .module('horizon.framework.util.file')
    .factory('horizon.framework.util.file.text-download',
      textDownloadService);

  textDownloadService.$inject = ['$q', '$timeout'];

  /**
   * @ngdoc service
   * @name horizon.framework.util.file.textDownloadService
   * @description
   * Service for download text contetns as file.  Used for client-side
   * text file creation and download, such as download a private key
   * file after key pair creation.
   */
  function textDownloadService($q, $timeout) {
    var service = {
      downloadTextFile: downloadTextFile
    };

    return service;

    ////////////////

    function downloadTextFile(text, filename) {
      // create text file as object url
      var blob = new Blob([ text ], { "type" : "text/plain" });
      window.URL = window.URL || window.webkitURL;
      var fileUrl = window.URL.createObjectURL(blob);

      // provide text as downloaded file
      var a = angular.element('<a></a>');
      a.attr("href", fileUrl);
      a.attr("download", filename);
      angular.element(document.body).append(a);

      var deferred = $q.defer();
      // start download after updating view
      $timeout(startDownload, 0);
      return deferred.promise;

      function startDownload() {
        a[0].click();
        a.remove();
        deferred.resolve(filename);
      }
    }
  }
})();
