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

  /**
   * @ngdoc directive
   * @name horizon.framework.widgets:loadEdit
   * @scope
   * @element
   * @description
   * The 'loadEdit' directive supports and validates size of the script entered
   *
   * @param {object} config
   * @param {object} userInput
   * @param {object} key
   *
   * See configuration.html for example usage.
   */
  angular
    .module('horizon.framework.widgets.load-edit')
    .directive('loadEdit', loadEdit);

  loadEdit.$inject = [
    '$timeout',
    'horizon.framework.util.file.file-reader',
    'horizon.framework.widgets.load-edit.basePath'
  ];

  function loadEdit($timeout, fileReader, basePath) {
    var directive = {
      restrict: 'E',
      scope: {
        config: '=',
        userInput: '=',
        key: '@'
      },
      link: link,
      templateUrl: basePath + 'load-edit.html'
    };

    return directive;

    ////////////////////

    function link($scope, $element) {
      var textarea = $element.find('textarea');
      var fileInput = $element.find('input[type="file"]');

      $scope.textContent = '';

      /* HTML5 file API is supported by IE10+, Chrome, FireFox and Safari (on Mac).
       *
       * If HTML5 file API is not supported by user's browser, remove the option
       * to upload a script via file upload.
       */
      $scope.config.fileApiSupported = !!FileReader;

      /* Angular won't fire change events when the <textarea> is in invalid
       * status, so we have to use jQuery/jqLite to watch for <textarea> changes.
       * If there are changes, we call the onScriptChange function to update the
       * size stats and perform validation.
       */
      textarea.on('input propertychange', onTextareaChange);
      fileInput.on('change', onFileLoad);

      function onTextareaChange() {
        $scope.$applyAsync(function () {
          /* Angular model won't provide the value of the <textarea> when it is in
           * invalid status, so we have to use jQuery or jqLite to get the length
           * of the <textarea> content.
           */
          $scope.scriptLength = textarea.val().length;
          $scope.userInput[$scope.key] = $scope.textContent;
          if ($scope.scriptLength > 0) {
            $scope.scriptModified = true;
          } else {
            $scope.scriptModified = false;
          }
        });
      }

      function onFileLoad(event) {
        var file = event.originalEvent.target.files[0];

        if (file) {
          fileReader.readTextFile(file).then(updateTextArea);
        }
      }

      function updateTextArea(fileContents) {
        $scope.textContent = fileContents;

        /* Once the DOM manipulation is done, update the scriptLength, so that
         * user knows the length of the script loaded into the <textarea>.
         */
        $timeout(function () {
          onTextareaChange();
          $scope.scriptModified = false;
        }, 250, false);

        // Focus the <textarea> element after injecting the code into it.
        textarea.focus();
      }

    }
  }
})();
