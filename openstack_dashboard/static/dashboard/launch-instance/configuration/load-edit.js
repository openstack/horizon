(function () {
  'use strict';

  angular.module('hz.dashboard.launch-instance')

  .directive('loadEdit', ['dashboardBasePath', '$timeout',
    function (path, $timeout) {

      function link($scope, $element) {
        var textarea = $element.find('textarea'),
            fileInput = $element.find('input[type="file"]'),
            userInput = $scope.userInput;

        $scope.textContent = '';

        // HTML5 file API is supported by IE10+, Chrome, FireFox and Safari (on Mac).
        //
        // If HTML5 file API is not supported by user's browser, remove the option
        // to upload a script via file upload.
        $scope.config.fileApiSupported = !!FileReader;

        function onTextareaChange() {
          $scope.$applyAsync(function () {
            // Angular model won't provide the value of the <textarea> when it is in
            // invalid status, so we have to use jQuery or jqLite to get the length
            // of the <textarea> content.

            $scope.scriptLength = textarea.val().length;
            $scope.userInput[$scope.key] = $scope.textContent;
            if ($scope.scriptLength > 0) {
              $scope.scriptModified = true;
            } else {
              $scope.scriptModified = false;
            }
          });
        }

        // Angular won't fire change events when the <textarea> is in invalid
        // status, so we have to use jQuery/jqLite to watch for <textarea> changes.
        // If there are changes, we call the onScriptChange function to update the
        // size stats and perform validation.
        textarea.on('input propertychange', onTextareaChange);

        function onFileLoad(event) {
          var file = event.originalEvent.target.files[0];

          if (file) {
            var reader = new FileReader();

            reader.onloadend = function (e) {
              $scope.$applyAsync(function () {
                var charArray = new Uint8Array(e.target.result);

                $scope.textContent = [].map.call(charArray,
                  function (char) {
                    return String.fromCharCode(char);
                  }
                ).join('');
              });
            };

            reader.readAsArrayBuffer(file.slice(0, file.size));

            // Once the DOM manipulation is done, update the scriptLength, so that
            // user knows the length of the script loaded into the <textarea>.
            $timeout(function () {
              onTextareaChange();
              $scope.scriptModified = false;
            }, 250, false);

            // Focus the <textarea> element after injecting the code into it.
            textarea.focus();
          }
        }

        fileInput.on('change', onFileLoad);
      }

      return {
        restrict: 'E',
        scope: {
          config: '=',
          userInput: '=',
          key: '@'
        },
        link: link,
        templateUrl: path + 'launch-instance/configuration/load-edit.html'
      };
    }
  ])

;})();
