/**
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

(function () {
  'use strict';

  angular
    .module('horizon.framework.conf', [])
    .constant('horizon.framework.conf.spinner_options', {
      inline: {
        lines:  10,
        length: 5,
        width:  2,
        radius: 3,
        color:  '#000',
        speed:  0.8,
        trail:  50,
        zIndex: 100
      },
      modal: {
        lines:  10,
        length: 15,
        width:  4,
        radius: 10,
        color:  '#000',
        speed:  0.8,
        trail:  50
      },
      line_chart: {
        lines:  10,
        length: 15,
        width:  4,
        radius: 11,
        color:  '#000',
        speed:  0.8,
        trail:  50
      }
    })
    .value('horizon.framework.conf.toastOptions', {
      'delay': 3000,
      'dimissible': ['alert-success', 'alert-info']
    });
})();
