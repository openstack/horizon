/* This is the base Horizon JavaScript object. There is only ever one of these
 * loaded (referenced as horizon with a lower-case h) which happens immediately
 * after the definition below.
 *
 * Scripts that are dependent on functionality defined in the Horizon object
 * must be included after this script in templates/base.html.
 */
var Horizon = function() {
  var horizon = {};
  var initFunctions = [];

  /* Use the addInitFunction() function to add initialization code which must
   * be called on DOM ready. This is useful for adding things like event
   * handlers or any other initialization functions which should preceed user
   * interaction but rely on DOM readiness.
   */
  horizon.addInitFunction = function(fn) {
    initFunctions.push(fn);
  };

  /* Call all initialization functions and clear the queue. */
  horizon.init = function() {
    // Load client-side template fragments and compile them.
    horizon.templates.compile_templates();

    // Bind event handlers to confirm dangerous actions.
    $("body").on("click", "form button.btn-danger", function (evt) {
      horizon.datatables.confirm(this);
      evt.preventDefault();
    });

    // Bind dismiss(x) handlers for alert messages.
    $(".alert").alert();

    $.each(initFunctions, function(ind, fn) {
      fn();
    });

    // Prevent multiple executions, just in case.
    initFunctions = [];
  };

  /* Convenience functions for dealing with namespaced Horizon cookies. */
  horizon.cookies = {
    read: function (cookie_name) {
      // Read in a cookie which contains JSON, and return a parsed object.
      var cookie = $.cookie("horizon." + cookie_name);
      if (cookie === null) {
        return {};
      }
      return $.parseJSON(cookie);
    },
    write: function (cookie_name, data) {
      // Overwrites a cookie.
      $.cookie("horizon." + cookie_name, JSON.stringify(data), {path: "/"});
    },
    update: function (cookie_name, key, value) {
      var data = horizon.cookies.read("horizon." + cookie_name);
      data[key] = value;
      horizon.cookies.write(cookie_name, data);
    },
    delete: function (cookie_name) {
      $.cookie("horizon." + cookie_name, null);
    }
  };

  /* Namespace for core functionality related to Forms. */
  horizon.forms = {
    handle_source_group: function() {
      // Delegate this handler to form, so it only should be init once
      $("form").live("change", "#id_source_group", function(evt) {
        var $sourceGroup = $(this).find('#id_source_group');
        var $cidrContainer = $(this).find('#id_cidr').parent().parent();
        if($sourceGroup.val() === "") {
          $cidrContainer.removeClass("hide");
        } else {
          $cidrContainer.addClass("hide");
        }
      });
    }
  };

  /* Namespace for core functionality related to DataTables. */
  horizon.datatables = {
    update: function () {
      var $rows_to_update = $('tr.status_unknown.ajax-update');
      if ($rows_to_update.length) {
        var interval = $rows_to_update.attr('data-update-interval'),
            $table = $rows_to_update.closest('table'),
            decay_constant = $table.attr('decay_constant');

        // Do not update this row if the action column is expanded
        if ($rows_to_update.find('.actions_column .btn-group.open').length) {
          // Wait and try to update again in next interval instead
          setTimeout(horizon.datatables.update, interval);
          // Remove interval decay, since this will not hit server
          $table.removeAttr('decay_constant');
          return;
        }
        // Trigger the update handlers.
        $rows_to_update.each(function(index, row) {
          var $row = $(this),
              $table = $row.closest('table');
          horizon.ajax.queue({
            url: $row.attr('data-update-url'),
            error: function (jqXHR, textStatus, errorThrown) {
              switch (jqXHR.status) {
                // A 404 indicates the object is gone, and should be removed from the table
                case 404:
                  // Update the footer count and reset to default empty row if needed
                  var $footer = $table.find('tr:last'),
                      row_count, footer_text, colspan, template, params, $empty_row;

                  // existing count minus one for the row we're removing
                  row_count = $table.find('tbody tr').length - 1;
                  footer_text = "Displaying " + row_count + " item";
                  if(row_count !== 1) {
                      footer_text += 's';
                  }
                  $footer.find('span').text(footer_text);

                  if(row_count === 0) {
                    colspan = $footer.find('td').attr('colspan');
                    template = horizon.templates.compiled_templates["#empty_row_template"];
                    params = {"colspan": colspan};
                    empty_row = template.render(params);
                    $row.replaceWith(empty_row);
                  } else {
                    $row.remove();
                  }
                  break;
                default:
                  if (horizon.conf.debug) {
                    horizon.alert("error", "An error occurred while updating.");
                  }
                  $row.removeClass("ajax-update");
                  $row.find("i.ajax-updating").remove();
                  break;
              }
            },
            success: function (data, textStatus, jqXHR) {
              var $new_row = $(data);
              if($new_row.hasClass('status_unknown')) {
                // only add spinning animation if row needs update
                var spinner = '<i class="icon-updating ajax-updating"></i>';
                $new_row.find("td.status_unknown").prepend(spinner);
              }
              // Only replace row if the html content has changed
              if($new_row.html() != $row.html()) {
                if($row.find(':checkbox').is(':checked')) {
                  // Preserve the checkbox if it's already clicked
                  $new_row.find(':checkbox').prop('checked', true);
                }
                $row.replaceWith($new_row);
                // Reset decay constant.
                $table.removeAttr('decay_constant');
              }
            },
            complete: function (jqXHR, textStatus) {
              // Revalidate the button check for the updated table
              horizon.datatables.validate_button();
            }
          });
        });

        // Set interval decay to this table, and increase if it already exist
        if(decay_constant === undefined) {
          decay_constant = 1;
        } else {
          decay_constant++;
        }
        $table.attr('decay_constant', decay_constant);
        // Poll until there are no rows in an "unknown" state on the page.
        next_poll = interval * decay_constant;
        // Limit the interval to 30 secs
        if(next_poll > 30 * 1000) next_poll = 30 * 1000;
        setTimeout(horizon.datatables.update, next_poll);
      }
    },

    validate_button: function () {
      // Disable form button if checkbox are not checked
      $("form").each(function (i) {
        var checkboxes = $(this).find(":checkbox");
        if(!checkboxes.length) {
          // Do nothing if no checkboxes in this form
          return;
        }
        if(!checkboxes.filter(":checked").length) {
          $(this).find(".table_actions button.btn-danger").addClass("disabled");
        }
      });

      $("form :checkbox").on("click", function (evt) {
        var $form = $(this).closest("form");
        var any_checked = $form.find("tbody :checkbox").is(":checked");

        // Enable the button if any checkbox is checked,
        // Disable if all checkbox is cleared
        if(any_checked) {
          $form.find(".table_actions button.btn-danger").removeClass("disabled");
        }else {
          $form.find(".table_actions button.btn-danger").addClass("disabled");
        }
      });
    }
  };

  /* Generates a confirmation modal dialog for the given action. */
  horizon.datatables.confirm = function (action) {
    var $action = $(action),
        $modal_parent = $(action).closest('.modal'),
        action_string, title, body, modal, form;
    if($action.hasClass("disabled")) {
      return;
    }
    action_string = $action.text();
    title = "Confirm " + action_string;
    body = "Please confirm your selection. This action cannot be undone.";
    modal = horizon.modals.create(title, body, action_string);
    modal.modal();
    if($modal_parent.length) {
      var child_backdrop = modal.next('.modal-backdrop');
      // re-arrange z-index for these stacking modal
      child_backdrop.css('z-index', $modal_parent.css('z-index')+10);
      modal.css('z-index', child_backdrop.css('z-index')+10);
    }
    modal.find('.btn-primary').click(function (evt) {
      form = $action.closest('form');
      form.append("<input type='hidden' name='" + $action.attr('name') + "' value='" + $action.attr('value') + "'/>");
      form.submit();
      modal.modal('hide');
      return false;
    });
    return modal;
  };

  /* Namespace for core functionality related to client-side templating. */
  horizon.templates = {
    template_ids: ["#modal_template", "#empty_row_template", "#alert_message_template"],
    compiled_templates: {}
  };

  /* Pre-loads and compiles the client-side templates. */
  horizon.templates.compile_templates = function () {
    $.each(horizon.templates.template_ids, function (ind, template_id) {
      horizon.templates.compiled_templates[template_id] = Hogan.compile($(template_id).text());
    });
  };

  /* Namespace for core functionality related to modal dialogs. */
  horizon.modals = {};

  /* Creates a modal dialog from the client-side template. */
  horizon.modals.create = function (title, body, confirm, cancel) {
    if (!cancel) {
      cancel = "Cancel";
    }
    var template = horizon.templates.compiled_templates["#modal_template"],
        params = {title: title, body: body, confirm: confirm, cancel: cancel},
        modal = $(template.render(params)).appendTo("body");
    return modal;
  };

  /* Utilities for common needs which aren't JS builtins. */
  horizon.utils = {
    capitalize: function(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }
  };

  horizon.instances = {
    user_decided_length: false,

    getConsoleLog: function(form_element, via_user_submit) {
      if(this.user_decided_length) {
        var data = $(form_element).serialize();
      } else {
        var data = "length=35";
      }

      $.ajax({
        url: $(form_element).attr('action'),
        data: data,
        method: 'get',
        success: function(response_body) {
          $('pre.logs').text(response_body);
        },
        error: function(response) {
          if(via_user_submit) {
            horizon.clearErrorMessages();

            horizon.alert('error', 'There was a problem communicating with the server, please try again.');
          }
        }
      });
    }
  };

  horizon.alert = function (type, message) {
    var template = horizon.templates.compiled_templates["#alert_message_template"],
        params = {"type": type,
                  "type_capitalized": horizon.utils.capitalize(type),
                  "message": message};
    return $(template.render(params)).prependTo("#main_content .messages");
  };

  horizon.clearErrorMessages = function() {
    $('#main_content .messages .alert.alert-error').remove()
  };

  /* Queued ajax handling for Horizon.
   *
   * Note: The number of concurrent AJAX connections hanlded in the queue
   * can be configured by setting an "ajax_queue_limit" key in
   * settings.HORIZON_CONFIG to the desired number (or None to disable queue
   * limiting).
   */
  horizon.ajax = {
    // This will be our jQuery queue container.
    _queue: [],
    _active: [],
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

  return horizon;
};

// Create the one and only horizon object.
var horizon = Horizon();

// Call init on DOM ready.
$(document).ready(horizon.init);
