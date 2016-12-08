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
    var def = $.Deferred();
    horizon.ajax._queue.push({opts: opts, deferred: def});
    // Start up the queue handler in case it's stopped.
    horizon.ajax.next();
    return def.promise();
  },
  next: function () {
    var queue = horizon.ajax._queue;
    var limit = horizon.conf.ajax.queue_limit;

    function process_queue(request) {
      return function() {
        // TODO(sambetts) Add some processing for error cases
        // such as unauthorised etc.
        var active = horizon.ajax._active;
        var index = $.inArray(request, active);
        if (index > -1) {
          active.splice(index, 1);
        }
        horizon.ajax.next();
      };
    }

    if (queue.length && (!limit || horizon.ajax._active.length < limit)) {
      var item = queue.shift();
      var request = $.ajax(item.opts);
      horizon.ajax._active.push(request);

      // Add an always callback that processes the next part of the queue,
      // as well as success and fail callbacks that resolved/rejects
      // the deferred.
      request.always(process_queue(request));
      request.then(item.deferred.resolve, item.deferred.reject);
    }
  }
};
