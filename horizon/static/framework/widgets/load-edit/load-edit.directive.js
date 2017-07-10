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
   * @name horizon.framework.widgets:load-edit
   * @scope
   * @element
   * @description
   * The 'load-edit' directive supports and validates size of the text entered
   *
   * @param {object} title
   * @param {object} model
   * @param {object} maxBytes
   * @param {object} key
   * @param {object} required
   * @param {object} rows
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
        title: '@',
        model: '=',
        maxBytes: '@',
        key: '@',
        required: '=',
        rows: '@',
        onTextareaChange: '&'
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
       * to upload a text via file upload.
       */
      $scope.fileApiSupported = !!FileReader;

      /* Angular won't fire change events when the <textarea> is in invalid
       * status, so we have to use jQuery/jqLite to watch for <textarea> changes.
       * If there are changes, we call the onTextareaChange function to update the
       * size stats and perform validation.
       */
      textarea.on('input propertychange', onTextareaChange);
      fileInput.on('change', onFileLoad);

      /* onchange event occurs when a control loses the input focus and
       * its value has been modified since gaining focus so we need to clear
       * up the fileInput.val() when the textContent field is modified as to
       * allow reloading the same text.
       */
      var textContentWatcher = $scope.$watch(function () {
        return $scope.textContent;
      }, function () {
        if (fileInput.val() !== "") {
          fileInput.val(null);
        }
      }, true);

      $scope.$on('$destroy', function() {
        textContentWatcher();
      });

      function onTextareaChange() {
        $scope.$applyAsync(function () {
          /* Angular model won't provide the value of the <textarea> when it is in
           * invalid status, so we have to use jQuery or jqLite to get the length
           * of the <textarea> content.
           */
          $scope.textBytes = getStrByte(textarea.val());
          $scope.model = $scope.textContent;
          if ($scope.textBytes > 0) {
            $scope.textModified = true;
          } else {
            $scope.textModified = false;
          }
          $scope.onTextareaChange({textContent: $scope.textContent});
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

        /* Once the DOM manipulation is done, update the textBytes, so that
         * user knows the bytes of the text loaded into the <textarea>.
         */
        $timeout(function () {
          onTextareaChange();
          $scope.textModified = false;
        }, 250, false);

        // Focus the <textarea> element after injecting the code into it.
        textarea.focus();
      }

      /* The length property for string shows only number of character.
       * If text includes multibyte string, it doesn't mean number of bytes.
       * So to count bytes, convert to Blob object and get its size.
       */
      function getStrByte(str) {
        return (new Blob([str], {type: "text/plain"})).size;
      }
    }
  }
})();
