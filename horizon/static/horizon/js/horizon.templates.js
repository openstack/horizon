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
