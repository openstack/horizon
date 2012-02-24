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

  /* Namespace for core functionality related to DataTables. */
  horizon.datatables = {
    update: function () {
      var rows_to_update = $('tr.status_unknown');
      if (rows_to_update.length) {
        // Trigger the update handler.
        var $updaters = rows_to_update.find('.ajax-update');
        $updaters.click();
        // Poll until there are no rows in an "unknown" state on the page.
        setTimeout(horizon.datatables.update, $updaters.attr('data-update-interval'));
      }
    }
  };

  /* Generates a confirmation modal dialog for the given action. */
  horizon.datatables.confirm = function (action) {
    var $action = $(action),
        action_string, title, body, modal, form;
    action_string = $action.text();
    title = "Confirm " + action_string;
    body = "Please confirm your selection. This action cannot be undone.";
    modal = horizon.modals.create(title, body, action_string);
    modal.modal('show');
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
