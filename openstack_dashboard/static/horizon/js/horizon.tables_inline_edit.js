/**
* Rewrite of horizon.tables_inline_edit.js to use list-groups and list-group-items
* instead of tables
*/
horizon.inline_edit = {
  get_cell_id: function (cell_div_element) {
    return [
      cell_div_element.parents("div.inline_edit_available").first().data("object-id"),
      "__",
      cell_div_element.data("cell-name")
    ].join('');
  },
  get_object_container: function (cell_div_element) {
    // global cell object container
    if (!window.cell_object_container) {
      window.cell_object_container = [];
    }
    return window.cell_object_container;
  },
  get_cell_object: function (cell_div_element) {
    var cell_id = horizon.inline_edit.get_cell_id(cell_div_element);
    var id = "cell__" + cell_id;
    var container = horizon.inline_edit.get_object_container(cell_div_element);
    var cell_object;
    if (container && container[id]){
      // if cell object exists, I will reuse it
      cell_object = container[id];
      cell_object.reset_with(cell_div_element);
      return cell_object;
    } else {
      // or I will create new cell object
      cell_object = new horizon.inline_edit.Cell(cell_div_element);
      // saving cell object to global container
      container[id] = cell_object;
      return cell_object;
    }
  },
  Cell: function (cell_div_element){
    var self = this;

    // setting initial attributes
    self.reset_with = function(cell_div_element){
      self.cell_div_element = cell_div_element;
      self.form_element = cell_div_element.find("input, textarea");
      self.url = cell_div_element.data('update-url');
      self.inline_edit_mod = false;
      self.successful_update = false;
    };
    self.reset_with(cell_div_element);

    self.refresh = function () {
      horizon.ajax.queue({
        url: self.url,
        data: {'inline_edit_mod': self.inline_edit_mod},
        beforeSend: function () {
          self.start_loading();
        },
        complete: function () {
          // Bug in Jquery tool-tip, if I hover tool-tip, then confirm the field with
          // enter and the cell is reloaded, tool-tip stays. So just to be sure, I am
          // removing tool-tips manually
          $(".tooltip.fade.top.in").remove();
          self.stop_loading();

          if (self.successful_update) {
            // if cell was updated successfully, I will show fading check sign
            var success = $('<div class="success"></div>');
            self.cell_div_element.find('.inline-edit-status').append(success);

            var background_color = self.cell_div_element.css('background-color');

            // edit pencil will disappear and appear again once the check sign has faded
            // also green background will disappear
            self.cell_div_element.addClass("no-transition");
            self.cell_div_element.addClass("success");
            self.cell_div_element.removeClass("no-transition");

            self.cell_div_element.removeClass("inline_edit_available");

            success.fadeOut(1300, function () {
              self.cell_div_element.addClass("inline_edit_available");
              self.cell_div_element.removeClass("success");
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
          var cell_div_element = $(data);
          self.form_element = self.get_form_element(cell_div_element);

          if (self.inline_edit_mod) {
            // if cell is in inline edit mode
            var table_cell_wrapper = cell_div_element.find(".table_cell_wrapper");

            width = self.cell_div_element.outerWidth();
            height = self.cell_div_element.outerHeight();

            cell_div_element.width(width);
            cell_div_element.height(height);
            cell_div_element.css('margin', 0).css('padding', 0);
            table_cell_wrapper.css('margin', 0).css('padding', 0);

            if (self.form_element.attr('type') === 'checkbox'){
              var inline_edit_form = cell_div_element.find(".inline-edit-form");
              inline_edit_form.css('padding-top', '11px').css('padding-left', '4px');
              inline_edit_form.width(width - 40);
            } else {
              // setting CSS of element, so the cell remains the same size in editing mode
              self.form_element.width(width - 40);
              self.form_element.height(height - 2);
              self.form_element.css('margin', 0).css('padding', 0);
            }
          }
          // saving old cell_div_element for cancel and loading purposes
          self.cached_presentation_view = self.cell_div_element;
          // replacing old td with the new td element returned from the server
          self.rewrite_cell(cell_div_element);
          // focusing the form element inside the cell
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
            if (self.cell_div_element.find(".inline-edit-error .error").length <= 0) {
              self.form_element.css('padding-left', '20px');
              self.form_element.width(self.form_element.width() - 20);
            }
            // obtain the error message from response body
            error_message = $.parseJSON(jqXHR.responseText).message;
            // insert the error icon
            var error = $('<div title="' + error_message + '" class="error"></div>');
            self.cell_div_element.find(".inline-edit-error").html(error);
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
      self.rewrite_cell(self.cached_presentation_view);
      self.stop_loading();
    };
    self.get_form_element = function(cell_div_element){
      return cell_div_element.find("input, textarea");
    };
    self.rewrite_cell = function(cell_div_element){
      self.cell_div_element.replaceWith(cell_div_element);
      self.cell_div_element = cell_div_element;
    };
    self.start_loading = function() {
      self.cell_div_element.addClass("no-transition");

      var spinner = $('<div class="loading"></div>');
      self.cell_div_element.find('.inline-edit-status').append(spinner);
      self.cell_div_element.addClass("loading");
      self.cell_div_element.removeClass("inline_edit_available");
      self.get_form_element(self.cell_div_element).attr("disabled", "disabled");
    };
    self.stop_loading = function() {
      self.cell_div_element.find('div.inline-edit-status div.loading').remove();
      self.cell_div_element.removeClass("loading");
      self.cell_div_element.addClass("inline_edit_available");
      self.get_form_element(self.cell_div_element).removeAttr("disabled");
    };
  }
};


horizon.addInitFunction(function() {
  $('div.list-group').on('click', '.ajax-inline-edit', function (evt) {
    var $this = $(this);
    var cell_div_element = $this.parents('div.inline_edit_available').first();

    var cell = horizon.inline_edit.get_cell_object(cell_div_element);
    cell.inline_edit_mod = true;
    cell.refresh();

    evt.preventDefault();
  });

  var submit_form = function(evt, el){
    var $submit = $(el);
    var cell_div_element = $submit.parents('div.inline_edit_available').first();
    var post_data = $submit.parents('form').first().serialize();

    var cell = horizon.inline_edit.get_cell_object(cell_div_element);
    cell.update(post_data);

    evt.preventDefault();
  };

  $('div.list-group').on('click', '.inline-edit-submit', function (evt) {
    submit_form(evt, this);
  });

  $('div.list-group').on('keypress', '.inline-edit-form', function (evt) {
    if (evt.which === 13 && !evt.shiftKey) {
      submit_form(evt, this);
    }
  });

  $('div.list-group').on('click', '.inline-edit-cancel', function (evt) {
    var $cancel = $(this);
    var cell_div_element = $cancel.parents('div.inline_edit_available').first();

    var cell = horizon.inline_edit.get_cell_object(cell_div_element);
    cell.cancel();

    evt.preventDefault();
  });

  $('div.list-group').on('mouseenter', '.inline_edit_available', function (evt) {
    $(this).find(".table_cell_action").fadeIn(100);
  });

  $('div.list-group').on('mouseleave', '.inline_edit_available', function (evt) {
    $(this).find(".table_cell_action").fadeOut(200);
  });
});

