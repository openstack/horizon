/* global Hogan */
/* Namespace for core functionality related to client-side templating. */
horizon.templates = {
  template_ids: [
    "#modal_template",
    "#empty_row_template",
    "#alert_message_template",
    "#spinner-modal",
    "#membership_template",
    "#confirm_modal",
    "#progress-modal"
  ],
  compiled_templates: {}
};

/* Pre-loads and compiles the client-side templates. */
horizon.templates.compile_templates = function () {
  $.each(horizon.templates.template_ids, function (ind, template_id) {
    horizon.templates.compiled_templates[template_id] = Hogan.compile($(template_id).html());
  });
};

horizon.addInitFunction(horizon.templates.init = function () {
  // Load client-side template fragments and compile them.
  horizon.templates.compile_templates();
});
