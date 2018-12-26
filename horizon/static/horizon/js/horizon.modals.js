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

/* Namespace for core functionality related to modal dialogs.
 *
 * Modals in Horizon are treated as a "stack", e.g new ones are added to the
 * top of the stack, and they are always removed in a last-in-first-out
 * order. This allows for things like swapping between modals as part of a
 * workflow, for confirmations, etc.
 *
 * When a new modal is loaded into the DOM, it fires a "new_modal" event which
 * event handlers can listen for. However, for consistency, it is better to
 * add methods which should be run on instantiation of any new modal to be
 * applied via the horizon.modals.addModalInitFunction method.
 */
horizon.modals = {
  // Storage for our current jqXHR object.
  _request: null,
  spinner: null,
  progress_bar: null,
  _init_functions: []
};

horizon.modals.addModalInitFunction = function (f) {
  horizon.modals._init_functions.push(f);
};

horizon.modals.initModal = function (modal) {
  $(horizon.modals._init_functions).each(function (index, f) {
    f(modal);
  });
};

/* Creates a modal dialog from the client-side template. */
horizon.modals.create = function (title, body, confirm, cancel, confirmCssClass) {
  if (!cancel) {
    cancel = gettext("Cancel");
  }
  var template = horizon.templates.compiled_templates["#modal_template"],
    params = {
      title: title,
      body: body,
      confirm: confirm,
      cancel: cancel,
      confirmCssClass: confirmCssClass || "btn-primary",
      modal_backdrop: horizon.modals.MODAL_BACKDROP
    };
  return $(template.render(params)).appendTo("#modal_wrapper");
};

horizon.modals.success = function (data) {
  var modal;
  var modal_wrapper = $('#modal_wrapper');
  // Moves the modal_wrapper to the bottom. This shows it over other dialogs.
  modal_wrapper.parent().append(modal_wrapper);
  modal_wrapper.append(data);
  modal = $('#modal_wrapper > .modal:last');
  modal.modal();
  $(modal).trigger("new_modal", modal);
  return modal;
};

horizon.modals.modal_spinner = function (text, $container) {
  if (!$container) {
    $container = $('#modal_wrapper');
  }

  // Adds a spinner with the desired text in a modal window.
  horizon.modals.spinner = horizon.loader.modal(text);
  horizon.modals.spinner.appendTo($container);
  horizon.modals.spinner.modal({backdrop: 'static'});
};

horizon.modals.progress_bar = function (text) {
  var template = horizon.templates.compiled_templates["#progress-modal"];
  horizon.modals.bar = $(template.render({text: text}))
    .appendTo("#modal_wrapper");
  horizon.modals.bar.modal({backdrop: 'static'});

  var $progress_bar = horizon.modals.bar.find('.progress-bar');
  horizon.modals.progress_bar.update = function(fraction) {
    var percent = Math.round(100 * fraction) + '%';
    $progress_bar
      .css('width', Math.round(100 * fraction) + '%')
      .parents('.progress-text').find('.progress-bar-text').text(percent);
  };
};

horizon.modals.init_wizard = function () {
  // If workflow is in wizard mode, initialize wizard.
  var _max_visited_step = 0;
  var _validate_steps = function (start, end) {
    var $form = $('.workflow > form'),
      response = {};

    if (typeof end === 'undefined') {
      end = start;
    }

    // Clear old errors.
    if ($form.find('div.row div.alert-danger').siblings().length == 0) {
      $form.find('div.row div.alert-danger').parent().remove();
    } else {
      $form.find('div.row div.alert-danger').remove();
    }
    $form.find('.form-group.has-error').each(function () {
      var $group = $(this);
      $group.removeClass('has-error');
      $group.find('span.help-block').remove();
    });

    // Temporarilly remove "disabled" attribute to get the values serialized
    var disabled = $form.find('select[disabled="disabled"]').removeAttr("disabled");

    // Send the data for validation.
    $.ajax({
      type: 'POST',
      url: $form.attr('action'),
      headers: {
        'X-Horizon-Validate-Step-Start': start,
        'X-Horizon-Validate-Step-End': end
      },
      data: $form.serialize(),
      dataType: 'json',
      async: false,
      success: function (data) { response = data; }
    });

    // Re-enable the "disabled" attribute on disabled inputs.
    disabled.attr("disabled", "disabled");

    // Handle errors.
    if (response.has_errors) {
      var first_field = true;

      $.each(response.errors, function (step_slug, step_errors) {
        var step_id = response.workflow_slug + '__' + step_slug,
          $fieldset = $form.find('#' + step_id);
        $.each(step_errors, function (field, errors) {
          var $field;
          if (field === '__all__') {
            // Add global errors.
            $.each(errors, function (index, error) {
              $fieldset.find('div.row').prepend(
                '<div class="col-sm-12"><div class="alert alert-danger">' +
                error + '</div></div>');
            });
            $fieldset.find('input,  select, textarea').first().focus();
            return;
          }
          // Add field errors.
          $field = $fieldset.find('[name="' + field + '"]');
          $field.closest('.form-group').addClass('has-error');
          $.each(errors, function (index, error) {
            $field.closest(".form-control").after(
              '<span class="help-block">' +
              error + '</span>');
          });
          // Focus the first invalid field.
          if (first_field) {
            $field.focus();
            first_field = false;
          }
        });
      });

      return false;
    }
  };

  $('.workflow.wizard').bootstrapWizard({
    tabClass: 'wizard-tabs',
    nextSelector: '.button-next',
    previousSelector: '.button-previous',
    onTabShow: function (tab, navigation, index) {
      var $navs = navigation.find('li');
      var total = $navs.length;
      var current = index;
      var $footer = $('.modal-footer');
      _max_visited_step = Math.max(_max_visited_step, current);
      if (current + 1 >= total) {
        $footer.find('.button-next').hide();
        $footer.find('.button-final').show();
      } else {
        $footer.find('.button-next').show();
        $footer.find('.button-final').hide();
      }
      $navs.each(function(i) {
        var $this = $(this);
        if (i <= _max_visited_step) {
          $this.addClass('done');
        } else {
          $this.removeClass('done');
        }
      });
    },
    onNext: function ($tab, $nav, index) {
      return _validate_steps(index - 1);
    },
    onTabClick: function ($tab, $nav, current, index) {
      // Validate if moving forward, but move backwards without validation
      return (index <= current ||
              _validate_steps(current, index - 1) !== false);
    }
  });
};

horizon.modals.getUploadUrl = function(jqXHR) {
  return jqXHR.getResponseHeader("X-File-Upload-URL");
};

horizon.modals.fileUpload = function(url, file, jqXHR) {
  var token = jqXHR.getResponseHeader('X-Auth-Token');

  horizon.modals.progress_bar(gettext("Uploading image"));
  return $.ajax({
    type: 'PUT',
    url: url,
    xhrFields: {
      withCredentials: true
    },
    headers: {
      'X-Auth-Token': token
    },
    data: file,
    processData: false, // tell jQuery not to process the data
    contentType: 'application/octet-stream',
    xhr: function() {
      var xhr = new window.XMLHttpRequest();
      xhr.upload.addEventListener('progress', function(evt) {
        if (evt.lengthComputable) {
          horizon.modals.progress_bar.update(evt.loaded / evt.total);
        }
      }, false);
      return xhr;
    }
  });
};

horizon.modals.prepareFileUpload = function($form) {
  var $elem = $form.find('input[data-external-upload]');
  if (!$elem.length) {
    return undefined;
  }
  var file = $elem.get(0).files[0];
  var $hiddenPseudoFile = $form.find('input[name="' + $elem.attr('name') + '__hidden"]');
  if (file) {
    $hiddenPseudoFile.val(file.name);
    $elem.remove();
    return file;
  } else {
    $hiddenPseudoFile.val('');
    return undefined;
  }
};

horizon.addInitFunction(horizon.modals.init = function() {

  var $document = $(document);

  // Bind handler for initializing new modals.
  $('#modal_wrapper').on('new_modal', function (evt, modal) {
    horizon.modals.initModal(modal);
  });

  // Bind "cancel" button handler.
  $document.on('click', '.modal .cancel', function (evt) {
    $(this).closest('.modal').modal('hide');
    evt.preventDefault();
  });

  // AJAX form submissions from modals. Makes validation happen in-modal.
  $document.on('submit', '.modal form', function (evt) {
    var $form = $(this),
      form = this,
      $button = $form.find(".modal-footer .btn-primary"),
      update_field_id = $form.attr("data-add-to-field"),
      headers = {},
      modalFileUpload = $form.attr("enctype") === "multipart/form-data",
      formData, ajaxOpts, featureFileList, featureFormData, file;

    if (modalFileUpload) {
      featureFileList = $("<input type='file'/>").get(0).files !== undefined;
      featureFormData = window.FormData !== undefined;

      if (!featureFileList || !featureFormData) {
        // Test whether browser supports HTML5 FileList and FormData interfaces,
        // which make XHR file upload possible. If not, it doesn't
        // support setting custom headers in AJAX requests either, so
        // modal forms won't work in them (namely, IE9).
        return;
      } else {
        file = horizon.modals.prepareFileUpload($form);
        formData = new window.FormData(form);
      }
    } else {
      formData = $form.serialize();
    }
    evt.preventDefault();

    // Prevent duplicate form POSTs
    $button.prop("disabled", true);

    if (update_field_id) {
      headers["X-Horizon-Add-To-Field"] = update_field_id;
    }

    function processServerSuccess(data, textStatus, jqXHR) {
      var redirect_header = jqXHR.getResponseHeader("X-Horizon-Location"),
        add_to_field_header = jqXHR.getResponseHeader("X-Horizon-Add-To-Field"),
        json_data, field_to_update;
      if (redirect_header === null) {
        $('.ajax-modal, .dropdown-toggle').removeAttr("disabled");
      }

      if (redirect_header) {
        location.href = redirect_header;
      } else if (add_to_field_header) {
        json_data = $.parseJSON(data);
        field_to_update = $("#" + add_to_field_header);
        field_to_update.append("<option value='" + json_data[0] + "'>" + json_data[1] + "</option>");
        field_to_update.change();
        field_to_update.val(json_data[0]);
      } else {
        horizon.modals.success(data, textStatus, jqXHR);
      }
    }

    function processServerError(jqXHR, textStatus, errorThrown, $formElement) {
      $formElement = $formElement || $form;
      if (jqXHR.getResponseHeader('logout')) {
        location.href = jqXHR.getResponseHeader("X-Horizon-Location");
      } else {
        $('.ajax-modal, .dropdown-toggle').removeAttr("disabled");
        $formElement.closest(".modal").modal("hide");
        horizon.toast.add("danger", gettext("There was an error submitting the form. Please try again."));
      }
    }

    ajaxOpts = {
      type: "POST",
      url: $form.attr('action'),
      headers: headers,
      data: formData,
      beforeSend: function () {
        $("#modal_wrapper .modal").last().modal("hide");
        $('.ajax-modal, .dropdown-toggle').attr('disabled', true);
        horizon.modals.modal_spinner(gettext("Working"));
      },
      complete: function (jqXHR) {
        var redirect_header = jqXHR.getResponseHeader("X-Horizon-Location");
        if (redirect_header === null) {
          horizon.modals.spinner.modal('hide');
        }
        $("#modal_wrapper .modal").last().modal("show");
        $button.prop("disabled", false);
      },
      success: function (data, textStatus, jqXHR) {
        var promise;
        var uploadUrl = horizon.modals.getUploadUrl(jqXHR);
        $form.closest(".modal").modal("hide");
        if (uploadUrl) {
          promise = horizon.modals.fileUpload(uploadUrl, file, jqXHR);
        }
        if (promise) {
          promise.then(function() {
            // ignore data resolved in asyncUpload promise
            processServerSuccess(data, textStatus, jqXHR);
          }, function(jqXHR, statusText, errorThrown) {
            var $progressBar = horizon.modals.bar.find('.progress-bar');
            processServerError(jqXHR, statusText, errorThrown, $progressBar);
          });
        } else {
          processServerSuccess(data, textStatus, jqXHR);
        }
      },
      error: processServerError
    };

    if (modalFileUpload) {
      ajaxOpts.contentType = false;  // tell jQuery not to process the data
      ajaxOpts.processData = false;  // tell jQuery not to set contentType
    }
    $.ajax(ajaxOpts);
  });

  // Position modal so it's in-view even when scrolled down.
  $document.on('show.bs.modal', '.modal', function (evt) {
    // avoid closing the modal when escape is pressed on a select input
    $("select", evt.target).keyup(function (e) {
      if (e.keyCode === 27) {
        // remove the focus on the select, so double escape close the modal
        e.target.blur();
        e.stopPropagation();
      }
    });
  });

  // Focus the first usable form field in the modal for accessibility.
  horizon.modals.addModalInitFunction(function (modal) {
    $(modal).find(":text, select, textarea").filter(":visible:first").focus();
  });

  horizon.modals.addModalInitFunction(function(modal) {
    horizon.datatables.validate_button($(modal).find(".table_wrapper > form"));
  });

  // Compile angular directives in the modal DOM
  horizon.modals.addModalInitFunction(horizon.utils.loadAngular);

  // Load modals for ajax-modal links.
  $document.on('click', '.ajax-modal', function (evt) {
    var $this = $(this);

    // If there's an existing modal request open, cancel it out.
    if (horizon.modals._request && typeof(horizon.modals._request.abort) !== undefined) {
      horizon.modals._request.abort();
    }

    horizon.modals._request = $.ajax($this.attr('href'), {
      beforeSend: function () {
        horizon.modals.modal_spinner(gettext("Loading"));
      },
      complete: function () {
        // Clear the global storage;
        horizon.modals._request = null;
        horizon.modals.spinner.modal('hide');
      },
      error: function(jqXHR) {
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
            horizon.toast.add("danger", gettext("An error occurred. Please try again later."));
          }
        }
      },
      success: function (data, textStatus, jqXHR) {
        var update_field_id = $this.attr('data-add-to-field'),
          modal,
          form;
        modal = horizon.modals.success(data, textStatus, jqXHR);
        if (update_field_id) {
          form = modal.find("form");
          if (form.length) {
            form.attr("data-add-to-field", update_field_id);
          }
        }
      }
    });
    evt.preventDefault();
  });


  /* Manage the modal "stack" */

  // After a modal has been shown, hide any other modals that are already in
  // the stack. Only one modal can be visible at the same time.
  $document.on("show.bs.modal", ".modal", function () {
    var modal_stack = $("#modal_wrapper .modal");
    modal_stack.splice(modal_stack.length - 1, 1);
    modal_stack.modal("hide");
  });

  // After a modal has been fully hidden, remove it to avoid confusion.
  // Note: the modal should only be removed if it is the "top" of the stack of
  // modals, e.g. it's the one currently being interacted with and isn't just
  // temporarily being hidden.
  $document.on('hidden.bs.modal', '.modal', function () {
    var $this = $(this),
      modal_stack = $("#modal_wrapper .modal");
    if ($this[0] === modal_stack.last()[0] || $this.hasClass("loading")) {
      $this.remove();
      if (!$this.hasClass("loading")) {
        $("#modal_wrapper .modal").last().modal("show");
      }
    }
  });

  // Make modals draggable
  $document.on("show.bs.modal", ".modal", function () {
    $(".modal-content").draggable({
      handle: ".modal-header"
    });
  });

  // Helper class to show modal spinner on click
  // In case the event was generated by clicking any mouse button,
  // the normalized codes are matched according to http://api.jquery.com/event.which/
  var MOUSE_LBUTTON_CODE_NORMALIZED = 1;
  var MOUSE_WHEEL_CODE_NORMALIZED = 2;
  $(document).on('click', '.openstack-spin', function(ev) {
    // NOTE(tsufiev): prevent infinite 'Loading' spinner when opening link
    // in the other browser tab with mouse wheel or mouse lbutton + modifier
    if (ev.which !== MOUSE_WHEEL_CODE_NORMALIZED &&
        !(ev.which === MOUSE_LBUTTON_CODE_NORMALIZED &&
        (ev.shiftKey || ev.ctrlKey || ev.metaKey))) {
      horizon.modals.modal_spinner(gettext("Loading"));
    }
  });
});
