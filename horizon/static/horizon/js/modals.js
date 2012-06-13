/* Namespace for core functionality related to modal dialogs. */
horizon.modals = {
  // Storage for our current jqXHR object.
  _request: null,
  spinner: null,

  spinner_options: {
    lines:  10,
    length: 15,
    width:  4,
    radius: 10,
    color:  '#000',
    speed:  0.8,
    trail:  50
  }
};


/* Creates a modal dialog from the client-side template. */
horizon.modals.create = function (title, body, confirm, cancel) {
  if (!cancel) {
    cancel = "Cancel";
  }
  var template = horizon.templates.compiled_templates["#modal_template"],
    params = {title: title, body: body, confirm: confirm, cancel: cancel},
    modal = $(template.render(params)).appendTo("div.modal_wrapper");
  return modal;
};


horizon.modals.success = function (data, textStatus, jqXHR) {
  $('div.modal_wrapper').append(data);
  $('.modal span.help-block').hide();
  $('.modal:last').modal();

  horizon.datatables.validate_button();
};

horizon.addInitFunction(function() {
  $(document).on('click', '.modal .cancel', function (evt) {
    $(this).closest('.modal').modal('hide');
    evt.preventDefault();
  });

  $(document).on('submit', '.modal form', function (evt) {
    var $form = $(this),
        $button = $form.find(".modal-footer .btn-primary");
    if ($form.attr("enctype") === "multipart/form-data") {
      // AJAX-upload for files is not currently supported.
      return;
    }
    evt.preventDefault();

    // Prevent duplicate form POSTs
    $button.prop("disabled", true);

    $.ajax({
      type: "POST",
      url: $form.attr('action'),
      data: $form.serialize(),
      complete: function () {
        $button.prop("disabled", false);
      },
      success: function (data, textStatus, jqXHR) {
        // TODO(gabriel): This isn't a long-term solution for AJAX redirects.
        // https://blueprints.launchpad.net/horizon/+spec/global-ajax-communication
        var header = jqXHR.getResponseHeader("X-Horizon-Location");
        if (header) {
          location.href = header;
        }
        $form.closest(".modal").modal("hide");
        horizon.modals.success(data, textStatus, jqXHR);
      },
      error: function(jqXHR, status, errorThrown) {
        $form.closest(".modal").modal("hide");
        horizon.alert("error", "There was an error submitting the form. Please try again.");
      }
    });
  });

  // After a modal has been fully hidden, remove it to avoid confusion.
  $(document).on('hidden', '.modal', function () {
    $(this).remove();
  });

  $(document).on('show', '.modal', function(evt) {
    var scrollShift = $('body').scrollTop(),
        $this = $(this),
        topVal = $this.css('top');
    $this.css('top', scrollShift + parseInt(topVal, 10));
  });

  // Focus the first usable form field in the modal for accessibility.
  $('div.modal_wrapper').on('shown', '.modal', function(evt) {
    $(this).find(":text, select, textarea").filter(":visible:first").focus();
  });

  $('.ajax-modal').live('click', function (evt) {
    var $this = $(this);

    // If there's an existing modal request open, cancel it out.
    if (horizon.modals._request && typeof(horizon.modals._request.abort) !== undefined) {
      horizon.modals._request.abort();
    }

    horizon.modals._request = $.ajax($this.attr('href'), {
      beforeSend: function() {
        var template = horizon.templates.compiled_templates["#spinner-modal"];
        horizon.modals.spinner = $(template.render());

        horizon.modals.spinner.appendTo("div.modal_wrapper");
        horizon.modals.spinner.modal({backdrop: 'static'});
        horizon.modals.spinner.spin(horizon.modals.spinner_options);
      },
      complete: function () {
        // Clear the global storage;
        horizon.modals._request = null;
        horizon.modals.spinner.modal('hide');
      },
      error: function(jqXHR, status, errorThrown) {
        if (jqXHR.status === 401){
          var redir_url = jqXHR.getResponseHeader("X-Horizon-Location");
          if (redir_url){
            location.href = redir_url;
          } else {
            location.reload(true);
          }
        }
        else {
          if (!horizon.ajax.get_messages(jqXHR)) {
            // Generic error handler. Really generic.
            horizon.alert("error", "An error occurred. Please try again.");
          }
        }
      },
      success: horizon.modals.success
    });
    evt.preventDefault();
  });
});
