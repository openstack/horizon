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

/* This is the base Horizon JavaScript object. There is only ever one of these
 * loaded (referenced as horizon with a lower-case h) which happens immediately
 * after the definition below.
 *
 * Scripts that are dependent on functionality defined in the Horizon object
 * must be included after this script in templates/base.html.
 */
var Horizon = function () {
  var horizon = {},
      initFunctions = [];

  /* Use the addInitFunction() function to add initialization code which must
   * be called on DOM ready. This is useful for adding things like event
   * handlers or any other initialization functions which should precede user
   * interaction but rely on DOM readiness.
   */
  horizon.addInitFunction = function (fn) {
    initFunctions.push(fn);
  };

  /* Call all initialization functions and clear the queue. */
  horizon.init = function () {
    for (var i = 0; i < initFunctions.length; i += 1) {
      initFunctions[i]();
    }

    // Prevent multiple executions, just in case.
    initFunctions = [];
  };

  /* Storage for backend configuration variables which the frontend
   * should be aware of.
   */
  horizon.conf = {};

  // default languageCode for tests that run without Django context
  horizon.languageCode = 'en';

  return horizon;
};

// Create the one and only horizon object.
/*eslint-disable no-unused-vars */
var horizon = new Horizon();
/*eslint-enable no-unused-vars */
