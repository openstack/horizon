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

horizon.metering = {
  init_create_usage_report_form: function() {
    horizon.datepickers.add('input[data-date-picker]');
    horizon.metering.add_change_event_to_period_dropdown();
    horizon.metering.show_or_hide_date_fields();
  },
  init_stats_page: function() {
    if (typeof horizon.d3_line_chart !== 'undefined') {
      horizon.d3_line_chart.init("div[data-chart-type='line_chart']",
                                 {'auto_resize': true});
    }
    horizon.metering.add_change_event_to_period_dropdown();
    horizon.metering.show_or_hide_date_fields();
  },
  show_or_hide_date_fields: function() {
    $("#date_from .controls input, #date_to .controls input").val('');
    if ($("#id_period").find("option:selected").val() === "other"){
      $("#id_date_from, #id_date_to").parent().parent().show();
      return true;
    } else {
      $("#id_date_from, #id_date_to").parent().parent().hide();
      return false;
    }
  },
  add_change_event_to_period_dropdown: function() {
    $("#id_period").change(function(evt) {
        if (horizon.metering.show_or_hide_date_fields()) {
          evt.stopPropagation();
        }
    });
  }
};
