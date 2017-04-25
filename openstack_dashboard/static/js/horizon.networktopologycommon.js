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

// Aggregate for common network topology functionality
horizon.networktopologycommon = {
  init:function() {
    horizon.networktopologyloader.init();
    horizon.networktopologymessager.init();
  }
};

/**
 * Common data loader for network topology views
 */
horizon.networktopologyloader = {
  // data for the network topology views
  model: null,
  // timeout length
  reload_duration: 10000,
  // timer controlling update intervals
  update_timer: null,

  init:function() {
    var self = this;
    if($('#networktopology').length === 0) {
      return;
    }
    self.update();
  },

  /**
   * makes the data reqeuest and populates the 'model'
   */
  update:function() {
    var self = this;
    angular.element.getJSON(
      angular.element('#networktopology').data('networktopology') + '?' + angular.element.now(),
      function(data) {
        self.model = data;
        $('#networktopology').trigger('change');
        self.update_timer = setTimeout(function(){
          self.update();
        }, self.reload_duration);
      }
    );
  },

  /**
   * stops the data update sequences
   */
  stop_update:function() {
    var self = this;
    clearTimeout(self.update_timer);
  },

  // Set up loader template
  setup_loader: function($container) {
    return horizon.loader.inline(gettext('Loading')).hide().prependTo($container);
  }
};

/**
 * common utility for network topology view to create iframes and pass post
 * messages from those iframes
 */
horizon.networktopologymessager = {
  previous_message : null,
  // element to attach messages to
  post_messages:'#topologyMessages',
  // Array of functions to call when a message event is received
  messaging_functions: [],
  // data stored when a delete operation is finalizing
  delete_data: {},

  init:function() {
    var self = this;

    // listens for message events
    angular.element(window).on('message', function(e) {
      var message = angular.element.parseJSON(e.originalEvent.data);
      if (self.previous_message !== message.message) {
        horizon.toast.add(message.type, message.message);
        self.previous_message = message.message;
        self.delete_post_message(message.iframe_id);
        self.messageNotify(message);
        horizon.networktopologyloader.update();
        setTimeout(function() {
          self.previous_message = null;
          self.delete_data = {};
        },self.reload_duration);
      }
    });
  },

  /**
   * add method to be called when a message is received
   *
   * @param {function} fn method to be called
   *
   * @param {Object} fnObj object the method is being called from this make
   * sure the scope of 'this' is correct
   */
  addMessageHandler:function(fn, fnObj) {
    var self = this;
    self.messaging_functions.push({obj:fnObj, func:fn});
  },

  /**
   * calls the methods that subscribed to message notifications
   *
   * @param {Object} message iframe message content
   */
  messageNotify:function(message) {
    var self = this;
    for (var i = 0; i < self.messaging_functions.length; i += 1) {
      func = self.messaging_functions[i].func;
      fnObj = self.messaging_functions[i].obj;
      func.call(fnObj, message);
    }
  },

  /**
   * posts a message from the iframe
   *
   * @param {String} id target device id
   * @param {String} url URL for action
   * @param {Object} message object containing message value
   * @param {String} action value of action, e.g., "delete"
   * @param {Object} data of extra data that should be relayed with the message
   * notification
   */
  post_message: function(id,url,message,type,action,data) {
    var self = this;
    if(action == "delete") {
      self.delete_data.device_id = id;
      self.delete_data.device_type = type;
      self.delete_data.device_data = data;
    }

    // stop the update refesh cycle while action takes place
    horizon.networktopologyloader.stop_update();
    var iframeID = 'ifr_' + id;
    var iframe = $('<iframe width="500" height="300" />')
      .attr('id',iframeID)
      .attr('src',url)
      .appendTo('#topologyMessages');
    iframe.on('load',function() {
      angular.element(this).get(0).contentWindow.postMessage(
        JSON.stringify(message, null, 2), '*');
    });
  },

  // delete the iframe
  delete_post_message: function(id) {
    angular.element('#' + id).remove();
  }
};
