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
    .constant('protocols', ['binary', 'base64'])
    .constant('states', [gettext('Connecting'), gettext('Open'), gettext('Closing'), gettext('Closed')])

    /**
    * @ngdoc directive
    * @ngname serialConsole
    * 
    * @description
    * The serial-console element creates a terminal based on the widely-used term.js.
    * The "connection" attribute is input to a WebSocket object, which connects
    * to a server. In Horizon, this directive is used to connect to nova-serialproxy,
    * opening a serial console to any instance. Each key the user types is transmitted
    * to the instance, and each character the instance reponds with is displayed.
    */
    .directive('serialConsole', function(protocols, states) {
      return {
        scope: true,
        template: '<div id="terminalNode"></div><br>{{statusMessage()}}',
        restrict: 'E',
        link: function postLink(scope, element, attrs) {

          var connection = scope.$eval(attrs.connection);
          var term = new Terminal();
          var socket = new WebSocket(connection, protocols);

          socket.onerror = function() {
            scope.$apply(scope.status);
          };
          socket.onopen = function() {
            scope.$apply(scope.status);
            // initialize by "hitting enter"
            socket.send(String.fromCharCode(13));
          };
          socket.onclose = function() {
            scope.$apply(scope.status);
          };

          // turn the angular jQlite element into a raw DOM element so we can
          // attach the Terminal to it
          var termElement = angular.element(element)[0];
          term.open(termElement.ownerDocument.getElementById('terminalNode'));

          term.on('data', function(data) {
            socket.send(data);
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
    });
}());