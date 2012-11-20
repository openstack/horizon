/* Queued ajax handling for Horizon.
 *
 * Note: The number of concurrent AJAX connections hanlded in the queue
 * can be configured by setting an "ajax_queue_limit" key in
 * HORIZON_CONFIG to the desired number (or None to disable queue
 * limiting).
 */
horizon.ajax = {
  // This will be our jQuery queue container.
  _queue: [],
  _active: [],
  get_messages: function (request) {
    return request.getResponseHeader("X-Horizon-Messages");
  },
  // Function to add a new call to the queue.
  queue: function(opts) {
    var complete = opts.complete,
        active = horizon.ajax._active;

    opts.complete = function () {
      var index = $.inArray(request, active);
      if (index > -1) {
        active.splice(index, 1);
      }
      horizon.ajax.next();
      if (complete) {
        complete.apply(this, arguments);
      }
    };

    function request() {
      return $.ajax(opts);
    }

    // Queue the request
    horizon.ajax._queue.push(request);

    // Start up the queue handler in case it's stopped.
    horizon.ajax.next();
  },
  next: function () {
    var queue = horizon.ajax._queue,
        limit = horizon.conf.ajax.queue_limit,
        request;
    if (queue.length && (!limit || horizon.ajax._active.length < limit)) {
      request = queue.pop();
      horizon.ajax._active.push(request);
      return request();
    }
  }
};
