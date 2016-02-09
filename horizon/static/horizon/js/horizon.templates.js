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

/* global Hogan */
/* Namespace for core functionality related to client-side templating. */
horizon.templates = {
  template_ids: [
    "#modal_template",
    "#empty_row_template",
    "#alert_message_template",
    "#loader-modal",
    "#loader-inline",
    "#membership_template",
    "#confirm_modal",
    "#progress-modal"
  ],
  compiled_templates: {}
};

/* Pre-loads and compiles the client-side templates. */
horizon.templates.compile_templates = function (id) {

  // If an id is passed in, only compile that template
  if (id) {
    horizon.templates.compiled_templates[id] = Hogan.compile($(id).html());
  } else {
    // If its never been set, make it an empty object
    horizon.templates.compiled_templates =
      $.isEmptyObject(horizon.templates.compiled_templates) ? {} : horizon.templates.compiled_templates;

    // Over each template found, only recompile ones that need it
    $.each(horizon.templates.template_ids, function (ind, template_id) {
      if (!(template_id in horizon.templates.compiled_templates)) {
        horizon.templates.compiled_templates[template_id] = Hogan.compile($(template_id).html());
      }
    });
  }
};

/* Takes a template id, as defined in horizon.templates.template_ids, and returns the compiled
   template given the context passed in, as a jQuery object
 */
horizon.templates.compile = function(id, context) {
  var template = horizon.templates.compiled_templates[id];

  // If its not available, maybe we didn't compile it yet, try one more time
  if (!template) {
    horizon.templates.compile_templates(id);
    template = horizon.templates.compiled_templates[id];
  }
  return $(template.render(context));
};

horizon.addInitFunction(horizon.templates.init = function () {
  // Load client-side template fragments and compile them.
  horizon.templates.compile_templates();
});
