/*
 * Copyright 2015 Hewlett Packard Enterprise Development Company LP
 *
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
(function () {
  'use strict';

  angular
    .module('horizon.framework.util.file')
    .factory('horizon.framework.util.file.file-reader',
      fileReaderService);

  fileReaderService.$inject = ['$q'];

  /**
   * @ngdoc service
   * @name horizon.framework.util.file.fileReaderService
   * @description
   * Service for reading file contents.  Used for processing client-side
   * files, such as loading a config file into launch instance.
   *
   * readTextFile - reads a text file and returns a promise of its contents.
   */
  function fileReaderService($q) {
    var service = {
      readTextFile: readTextFile
    };

    return service;

    ////////////////

    function readTextFile(file, fileReader) {
      var reader = fileReader || new FileReader();
      var deferred = $q.defer();
      reader.onloadend = loadEnd;
      reader.readAsArrayBuffer(file.slice(0, file.size));
      return deferred.promise;

      function loadEnd(e) {
        var charArray = new Uint8Array(e.target.result);
        var textContent = [].map.call(charArray, strFromCharCode).join('');
        deferred.resolve(textContent);

        function strFromCharCode(char) {
          return String.fromCharCode(char);
        }
      }
    }
  }
})();
