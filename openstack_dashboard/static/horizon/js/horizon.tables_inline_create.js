/**
* Rewrite of horizon.tables_inline_edit.js to use list-groups and list-group-items
* instead of tables
*/
horizon.inline_edit = {
  get_action_id: function (action_div_element) {
    return [
      action_div_element.parents("div.inline_edit_available").first().data("object-id"),
      "__",
      action_div_element.data("action-name")
    ].join('');
  },
  get_object_container: function (action_div_element) {
    // global action object container
    if (!window.action_object_container) {
      window.action_object_container = [];
    }
    return window.action_object_container;
  },
  get_action_object: function (action_div_element) {
    var action_id = horizon.inline_edit.get_action_id(action_div_element);
    var id = "action__" + action_id;
    var container = horizon.inline_edit.get_object_container(action_div_element);
    var action_object;
    if (container && container[id]){
      // if action object exists, I will reuse it
      action_object = container[id];
      action_object.reset_with(action_div_element);
      return action_object;
    } else {
      // or I will create new action object
      action_object = new horizon.inline_edit.Cell(action_div_element);
      // saving action object to global container
      container[id] = action_object;
      return action_object;
    }
  },
  Cell: function (action_div_element){
    var self = this;

    // setting initial attributes
    self.reset_with = function(action_div_element){
      self.action_div_element = action_div_element;
      self.form_element = action_div_element.find("input, textarea");
      self.url = action_div_element.data('update-url');
      self.inline_edit_mod = false;
      self.successful_update = false;
    };
    self.reset_with(action_div_element);

    self.refresh = function () {
      horizon.ajax.queue({
        url: self.url,
        data: {'inline_edit_mod': self.inline_edit_mod},
        beforeSend: function () {
          self.start_loading();
        },
        complete: function () {
          // Bug in Jquery tool-tip, if I hover tool-tip, then confirm the field with
          // enter and the action is reloaded, tool-tip stays. So just to be sure, I am
          // removing tool-tips manually
          $(".tooltip.fade.top.in").remove();
          self.stop_loading();

          if (self.successful_update) {
            // if action was updated successfully, I will show fading check sign
            var success = $('<div class="success"></div>');
            self.action_div_element.find('.inline-edit-status').append(success);

            var background_color = self.action_div_element.css('background-color');

            // edit pencil will disappear and appear again once the check sign has faded
            // also green background will disappear
            self.action_div_element.addClass("no-transition");
            self.action_div_element.addClass("success");
            self.action_div_element.removeClass("no-transition");

            self.action_div_element.removeClass("inline_edit_available");

            success.fadeOut(1300, function () {
              self.action_div_element.addClass("inline_edit_available");
              self.action_div_element.removeClass("success");
            });
          }
        },
        error: function(jqXHR, status, errorThrown) {
          if (jqXHR.status === 401){
            var redir_url = jqXHR.getResponseHeader("X-Horizon-Location");
            if (redir_url){
              location.href = redir_url;
            } else {
              horizon.alert("error", gettext("Not authorized to do this operation."));
            }
          }
          else {
            if (!horizon.ajax.get_messages(jqXHR)) {
              // Generic error handler. Really generic.
              horizon.alert("error", gettext("An error occurred. Please try again later."));
            }
          }
        },
        success: function (data, textStatus, jqXHR) {
          var action_div_element = $(data);
          self.form_element = self.get_form_element(action_div_element);

          if (self.inline_edit_mod) {
            // if action is in inline edit mode
            var table_action_wrapper = action_div_element.find(".table_action_wrapper");

            width = self.action_div_element.outerWidth();
            height = self.action_div_element.outerHeight();

            action_div_element.width(width);
            action_div_element.height(height);
            action_div_element.css('margin', 0).css('padding', 0);
            table_action_wrapper.css('margin', 0).css('padding', 0);

            if (self.form_element.attr('type') === 'checkbox'){
              var inline_edit_form = action_div_element.find(".inline-edit-form");
              inline_edit_form.css('padding-top', '11px').css('padding-left', '4px');
              inline_edit_form.width(width - 40);
            } else {
              // setting CSS of element, so the action remains the same size in editing mode
              self.form_element.width(width - 40);
              self.form_element.height(height - 2);
              self.form_element.css('margin', 0).css('padding', 0);
            }
          }
          // saving old action_div_element for cancel and loading purposes
          self.cached_presentation_view = self.action_div_element;
          // replacing old td with the new td element returned from the server
          self.rewrite_action(action_div_element);
          // focusing the form element inside the action
          if (self.inline_edit_mod) {
            self.form_element.focus();
          }
        }
      });
    };
    self.update = function(post_data){
      // make the update request
      horizon.ajax.queue({
        type: 'POST',
        url: self.url,
        data: post_data,
        beforeSend: function () {
          self.start_loading();
        },
        complete: function () {
          if (!self.successful_update){
            self.stop_loading();
          }
        },
        error: function(jqXHR, status, errorThrown) {
          if (jqXHR.status === 400){
            // make place for error icon, only if the error icon is not already present
            if (self.action_div_element.find(".inline-edit-error .error").length <= 0) {
              self.form_element.css('padding-left', '20px');
              self.form_element.width(self.form_element.width() - 20);
            }
            // obtain the error message from response body
            error_message = $.parseJSON(jqXHR.responseText).message;
            // insert the error icon
            var error = $('<div title="' + error_message + '" class="error"></div>');
            self.action_div_element.find(".inline-edit-error").html(error);
            error.tooltip({'placement':'top'});
          }
          else if (jqXHR.status === 401){
            var redir_url = jqXHR.getResponseHeader("X-Horizon-Location");
            if (redir_url){
              location.href = redir_url;
            } else {
              horizon.alert("error", gettext("Not authorized to do this operation."));
            }
          }
          else {
            if (!horizon.ajax.get_messages(jqXHR)) {
              // Generic error handler. Really generic.
              horizon.alert("error", gettext("An error occurred. Please try again later."));
            }
          }
        },
        success: function (data, textStatus, jqXHR) {
          // if update was successful
          self.successful_update = true;
          self.refresh();
        }
      });
    };
    self.cancel = function() {
      self.rewrite_action(self.cached_presentation_view);
      self.stop_loading();
    };
    self.get_form_element = function(action_div_element){
      return action_div_element.find("input, textarea");
    };
    self.rewrite_action = function(action_div_element){
      self.action_div_element.replaceWith(action_div_element);
      self.action_div_element = action_div_element;
    };
    self.start_loading = function() {
      self.action_div_element.addClass("no-transition");

      var spinner = $('<div class="loading"></div>');
      self.action_div_element.find('.inline-edit-status').append(spinner);
      self.action_div_element.addClass("loading");
      self.action_div_element.removeClass("inline_edit_available");
      self.get_form_element(self.action_div_element).attr("disabled", "disabled");
    };
    self.stop_loading = function() {
      self.action_div_element.find('div.inline-edit-status div.loading').remove();
      self.action_div_element.removeClass("loading");
      self.action_div_element.addClass("inline_edit_available");
      self.get_form_element(self.action_div_element).removeAttr("disabled");
    };
  }
};


horizon.addInitFunction(function() {
  $('ul.list-group').on('click', '.ajax-inline-edit', function (evt) {
    var $this = $(this);
    var action_div_element = $this.parents('div.inline_edit_available').first();

    var action = horizon.inline_edit.get_action_object(action_div_element);
    action.inline_edit_mod = true;
    action.refresh();

    evt.preventDefault();
  });

  var submit_form = function(evt, el){
    var $submit = $(el);
    var action_div_element = $submit.parents('div.inline_edit_available').first();
    var post_data = $submit.parents('form').first().serialize();

    var action = horizon.inline_edit.get_action_object(action_div_element);
    action.update(post_data);

    evt.preventDefault();
  };

  $('ul.list-group').on('click', '.inline-edit-submit', function (evt) {
    submit_form(evt, this);
  });

  $('ul.list-group').on('keypress', '.inline-edit-form', function (evt) {
    if (evt.which === 13 && !evt.shiftKey) {
      submit_form(evt, this);
    }
  });

  $('ul.list-group').on('click', '.inline-edit-cancel', function (evt) {
    var $cancel = $(this);
    var action_div_element = $cancel.parents('div.inline_edit_available').first();

    var action = horizon.inline_edit.get_action_object(action_div_element);
    action.cancel();

    evt.preventDefault();
  });

  $('ul.list-group').on('mouseenter', '.inline_edit_available', function (evt) {
    $(this).find(".table_action_action").fadeIn(100);
  });

  $('ul.list-group').on('mouseleave', '.inline_edit_available', function (evt) {
    $(this).find(".table_action_action").fadeOut(200);
  });
});

