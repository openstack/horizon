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

  return horizon;
};

// Create the one and only horizon object.
/*eslint-disable no-unused-vars */
var horizon = new Horizon();
/*eslint-enable no-unused-vars */
