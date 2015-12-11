horizon.inline_edit = {
  get_cell_id: function (td_element) {
    return [
      td_element.parents("tr").first().data("object-id"),
      "__",
      td_element.data("cell-name")
    ].join('');
  },
  get_object_container: function () {
    // global cell object container
    if (!window.cell_object_container) {
      window.cell_object_container = [];
    }
    return window.cell_object_container;
  },
  get_cell_object: function (td_element) {
    var cell_id = horizon.inline_edit.get_cell_id(td_element);
    var id = "cell__" + cell_id;
    var container = horizon.inline_edit.get_object_container(td_element);
    var cell_object;
    if (container && container[id]){
      // if cell object exists, I will reuse it
      cell_object = container[id];
      cell_object.reset_with(td_element);
      return cell_object;
    } else {
      // or I will create new cell object
      cell_object = new horizon.inline_edit.Cell(td_element);
      // saving cell object to global container
      container[id] = cell_object;
      return cell_object;
    }
  },
  Cell: function (td_element){
    var self = this;

    // setting initial attributes
    self.reset_with = function(td_element){
      self.td_element = td_element;
      self.form_element = td_element.find("input, textarea");
      self.url = td_element.data('update-url');
      self.inline_edit_mod = false;
      self.successful_update = false;
    };
    self.reset_with(td_element);

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
            self.td_element.find('.inline-edit-status').append(success);

            // edit pencil will disappear and appear again once the check sign has faded
            // also green background will disappear
            self.td_element.addClass("no-transition");
            self.td_element.addClass("success");
            self.td_element.removeClass("no-transition");

            self.td_element.removeClass("inline_edit_available");

            success.fadeOut(1300, function () {
              self.td_element.addClass("inline_edit_available");
              self.td_element.removeClass("success");
            });
          }
        },
        error: function(jqXHR) {
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
        success: function (data) {
          var $td_element = $(data);
          var $tr, $cell_wrapper, td_element_text;
          self.form_element = self.get_form_element($td_element);

          if (self.inline_edit_mod) {
            var cellWidth = self.td_element.outerWidth(true);
            $td_element.width(cellWidth);
            $td_element.addClass("has-form");
          }
          // saving old td_element for cancel and loading purposes
          self.cached_presentation_view = self.td_element;
          // replacing old td with the new td element returned from the server
          self.rewrite_cell($td_element);
          // keeping parent tr's data-display attr up to date
          $tr = $td_element.closest('tr');
          if ($td_element.attr('data-cell-name') === $tr.attr('data-display-key')) {
            $cell_wrapper= $td_element.find('.table_cell_data_wrapper');
            if ($cell_wrapper.length) {
              td_element_text = $cell_wrapper.find('a').text();
              if ($tr.attr('data-display') !== td_element_text) {
                $tr.attr('data-display', td_element_text);
              }
            }
          }
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
        error: function(jqXHR) {
          if (jqXHR.status === 400){
            // make place for error icon, only if the error icon is not already present
            if (self.td_element.find(".inline-edit-error .error").length <= 0) {
              self.form_element.css('padding-left', '20px');
              self.form_element.width(self.form_element.width() - 20);
            }
            // obtain the error message from response body
            var error_message = $.parseJSON(jqXHR.responseText).message;
            // insert the error icon
            var error = $('<div title="' + error_message + '" class="error"></div>');
            self.td_element.find(".inline-edit-error").html(error);
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
        success: function () {
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
    self.get_form_element = function(td_element){
      return td_element.find("input, textarea");
    };
    self.rewrite_cell = function(td_element){
      self.td_element.replaceWith(td_element);
      self.td_element = td_element;
    };
    self.start_loading = function() {
      self.td_element.addClass("no-transition");

      var spinner = $('<div class="loading"></div>');
      self.td_element.find('.inline-edit-status').append(spinner);
      self.td_element.addClass("loading");
      self.td_element.removeClass("inline_edit_available");
      self.get_form_element(self.td_element).attr("disabled", "disabled");
    };
    self.stop_loading = function() {
      self.td_element.find('div.inline-edit-status div.loading').remove();
      self.td_element.removeClass("loading");
      self.td_element.addClass("inline_edit_available");
      self.get_form_element(self.td_element).removeAttr("disabled");
    };
  }
};


horizon.addInitFunction(horizon.inline_edit.init = function(parent) {
  parent = parent || document;
  var $table = $(parent).find('table');

  $table.on('click', '.ajax-inline-edit', function (evt) {
    var $this = $(this);
    var td_element = $this.parents('td').first();

    var cell = horizon.inline_edit.get_cell_object(td_element);
    cell.inline_edit_mod = true;
    cell.refresh();

    evt.preventDefault();
  });

  var submit_form = function(evt, el){
    var $submit = $(el);
    var td_element = $submit.parents('td').first();
    var post_data = $submit.parents('form').first().serialize();

    var cell = horizon.inline_edit.get_cell_object(td_element);
    cell.update(post_data);

    evt.preventDefault();
  };

  $table.on('click', '.inline-edit-submit', function (evt) {
    submit_form(evt, this);
  });

  $table.on('keypress', '.inline-edit-form', function (evt) {
    if (evt.which === 13 && !evt.shiftKey) {
      submit_form(evt, this);
    }
  });

  $table.on('click', '.inline-edit-cancel', function (evt) {
    var $cancel = $(this);
    var td_element = $cancel.parents('td').first();

    var cell = horizon.inline_edit.get_cell_object(td_element);
    cell.cancel();

    evt.preventDefault();
  });

  $table.on('mouseenter', '.inline_edit_available', function () {
    $(this).find(".table_cell_action").fadeIn(100);
  });

  $table.on('mouseleave', '.inline_edit_available', function () {
    $(this).find(".table_cell_action").fadeOut(200);
  });
});

