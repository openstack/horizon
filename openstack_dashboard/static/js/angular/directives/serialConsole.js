/*
Copyright 2014, Rackspace, US, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

/*global Terminal,Blob,FileReader,gettext,interpolate */
(function() {
  'use strict';

  angular.module('serialConsoleApp', [])
    .constant('states', [
      gettext('Connecting'),
      gettext('Open'),
      gettext('Closing'),
      gettext('Closed')
    ])

    /**
     * @ngdoc directive
     * @ngname serialConsole
     *
     * @description
     * The serial-console element creates a terminal based on the widely-used term.js.
     * The "connection" and "protocols" attributes are input to a WebSocket object,
     * which connects to a server. In Horizon, this directive is used to connect to
     * nova-serialproxy, opening a serial console to any instance. Each key the user
     * types is transmitted to the instance, and each character the instance reponds
     * with is displayed.
     */
    .directive('serialConsole', serialConsole);

  serialConsole.$inject = ['states', '$timeout'];

  function serialConsole(states, $timeout) {
    return {
      scope: true,
      template: '<div id="terminalNode"' +
        'termCols="{{termCols()}}" termRows="{{termRows()}}"></div>' +
        '<br>{{statusMessage()}}',
      restrict: 'E',
      link: function postLink(scope, element, attrs) {

        var connection = scope.$eval(attrs.connection);
        var protocols = scope.$eval(attrs.protocols);
        var term = new Terminal();
        var socket = new WebSocket(connection, protocols);

        socket.onerror = function() {
          scope.$apply(scope.status);
        };
        socket.onopen = function() {
          scope.$apply(scope.status);
          // initialize by "hitting enter"
          socket.send(str2ab(String.fromCharCode(13)));
        };
        socket.onclose = function() {
          scope.$apply(scope.status);
        };

        // turn the angular jQlite element into a raw DOM element so we can
        // attach the Terminal to it
        var termElement = angular.element(element)[0];
        term.open(termElement.ownerDocument.getElementById('terminalNode'));

        // default size of term.js
        scope.cols = 80;
        scope.rows = 24;
        // event handler to resize console according to window resize.
        angular.element(window).bind('resize', resizeTerminal);
        function resizeTerminal() {
          var terminal = angular.element('.terminal')[0];
          // take margin for scroll-bars on window.
          var winWidth = angular.element(window).width() - 30;
          var winHeight = angular.element(window).height() - 50;
          // calculate cols and rows.
          var newCols = Math.floor(winWidth / (terminal.clientWidth / scope.cols));
          var newRows = Math.floor(winHeight / (terminal.clientHeight / scope.rows));
          if ((newCols !== scope.cols || newRows !== scope.rows) && newCols > 0 && newRows > 0) {
            term.resize(newCols, newRows);
            scope.cols = newCols;
            scope.rows = newRows;
            // To set size into directive attributes for watched by outside,
            // termCols() and termRows() are needed to be execute for refreshing template.
            // NOTE(shu-mutou): But scope.$apply is not useful here.
            //                  "scope.$apply already in progress" error occurs at here.
            //                  So we need to use $timeout.
            $timeout(scope.termCols);
            $timeout(scope.termRows);
          }
        }
        // termCols and termRows provide console size into attribute of this directive.
        // NOTE(shu-mutou): setting scope variables directly on template definition seems
        //                  not to be effective for refreshing template.
        scope.termCols = function () {
          return scope.cols;
        };
        scope.termRows = function () {
          return scope.rows;
        };
        resizeTerminal();

        term.on('data', function(data) {
          socket.send(str2ab(data));
        });

        socket.onmessage = function(e) {
          if (e.data instanceof Blob) {
            var f = new FileReader();
            f.onload = function() {
              term.write(f.result);
            };
            f.readAsText(e.data);
          } else {
            term.write(e.data);
          }
        };

        scope.status = function() {
          return states[socket.readyState];
        };

        scope.statusMessage = function() {
          return interpolate(gettext('Status: %s'), [scope.status()]);
        };

        scope.$on('$destroy', function() {
          socket.close();
        });
      }
    };
  }

  function str2ab(str) {
    var buf = new ArrayBuffer(str.length); // 2 bytes for each char
    var bufView = new Uint8Array(buf);
    for (var i = 0, strLen = str.length; i < strLen; i++) {
      bufView[i] = str.charCodeAt(i);
    }
    return buf;
  }
}());
