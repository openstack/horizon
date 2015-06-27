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
