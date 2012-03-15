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
    $("body").on("click", "form .btn-danger", function (evt) {
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

  /* Namespace for core functionality related to Forms. */
  horizon.forms = {
    handle_source_group: function() {
      // Delegate this handler to form, so it only should be init once
      $("form").live("change", "#id_source_group", function(evt) {
        var $sourceGroup = $(this).find('#id_source_group');
        var $cidrContainer = $(this).find('#id_cidr').parent().parent();
        if($sourceGroup.val() == "") {
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
          var $row = $(this);
          $.ajax($row.attr('data-update-url'), {
            complete: function (jqXHR, status) {
              var $new_row = $(jqXHR.responseText);
              $new_row.find("td.status_unknown").prepend('<i class="icon-updating ajax-updating"></i>');
              // Only replace row if the html content has changed
              if($new_row.html() != $row.html()) {
                if($row.find(':checkbox').is(':checked')) {
                  // Preserve the checkbox if it's already clicked
                  $new_row.find(':checkbox').prop('checked', true);
                }
                $row.replaceWith($new_row);
                $table.removeAttr('decay_constant');
              }
              // Revalidate the button check for updated table
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
        var any_checked = $form.find(":checkbox").is(":checked");

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
        action_string, title, body, modal, form;
    if($action.hasClass("disabled")) {
      return;
    }
    action_string = $action.text();
    title = "Confirm " + action_string;
    body = "Please confirm your selection. This action cannot be undone.";
    var use_backdrop = !$('.modal').length; // check if already has a modal
    modal = horizon.modals.create(title, body, action_string);
    modal.modal({backdrop: use_backdrop});
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
    template_ids: ["#modal_template"],
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

  return horizon;
};

// Create the one and only horizon object.
var horizon = Horizon();

// Call init on DOM ready.
$(document).ready(horizon.init);
