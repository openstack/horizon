horizon.event_log = {
    cluster_id: null,
    data_update_url: null,
    cached_data: null,
    modal_step_id: null,

    fetch_update_events: function() {
        var url = this.data_update_url + "/events";
        $.get(url).done(function (data) {
            horizon.event_log.cached_data = data;
            horizon.event_log.update_view(data);
            horizon.event_log.schedule_next_update(data);
        }).fail(function() {
            // Event log is not available for some reason.
            horizon.alert("error", gettext("Event log is not available."));
        });
    },

    update_view: function (data) {
        this.update_step_rows(data.provision_steps);
        this.update_events_rows(data);
    },

    update_step_rows: function (steps) {
        // Clear steps
        $("#steps_body").find("tr").remove();

        $(steps).each(function (i, step) {
            horizon.event_log.create_step_row(step);
        });
    },

    create_step_row: function (step) {
        var step_row_template = "" +
            "<tr id='%step_id%'>" +
            "<td>%step_descr%</td>" +
            "<td>%started_at%</td>" +
            "<td>%duration%</td>" +
            "<td>%progress%</td>" +
            "<td>%result%&nbsp" +
            "<a data-target='#events_modal' data-toggle='modal' data-step-id='%step_id%' class='show_events_btn' id='%step_id%_show_events_btn'>" +
            gettext('Show events') + "</a>" +
            "</td>" +
            "</tr>";


        var started_at = new Date(step.created_at).toString();
        var progress = "" + step.completed + " / " + step.total;
        var description = step.step_type + "<br />" + step.step_name;

        var row = step_row_template
            .replace(/%step_id%/g, step.id)
            .replace(/%step_descr%/g, description)
            .replace(/%started_at%/g, started_at)
            .replace(/%duration%/g, step.duration)
            .replace(/%progress%/g, progress)
            .replace(/%result%/g, step.result);

        $("#steps_body").append(row);
        if (step.successful === true) {
            $("#" + step.id + "_show_events_btn").hide();
        }
    },

    update_events_rows: function(data) {
        if (!this.modal_step_id) {
            return;
        }
        var current_step = null;
        $(data.provision_steps).each(function (i, step) {
            if (step.id === horizon.event_log.modal_step_id) {
                current_step = step;
            }
        });

        var header = current_step.step_type + "<br />" + current_step.step_name;
        $("#events_modal_header").html(header);

        // Clear events
        this.clear_events();
        this.clear_modal_status();

        if (current_step.successful === true) {
            this.mark_modal_as_successful();
            return;
        }
        var events = current_step.events;
        $(events).each(function (i, event) {
            event.step_name = current_step.step_name;
        });

        $(events).each(function (i, event) {
            horizon.event_log.create_event_row(event);
        });

    },

    clear_events: function() {
        $("#events_body").find("tr").remove();
    },

    clear_modal_status: function() {
        $("#modal_status_marker").text("");
    },

    mark_modal_as_successful: function() {
        $("#modal_status_marker").text(gettext(
            "The step has completed successfully. No events to display."));
    },

    create_event_row: function(event) {
        var step_row_template = "" +
            "<tr id='%event_id%'>" +
            "<td>%node_group_name%</td>" +
            "<td>%instance%</td>" +
            "<td>%time%</td>" +
            "<td>%info%</td>" +
            "<td>%result%</td>" +
            "</tr>";

        var event_time = new Date(event.created_at).toString();

        var row = step_row_template
            .replace(/%event_id%/g, event.id)
            .replace(/%node_group_name%/g, event.node_group_name)
            .replace(/%instance%/g, event.instance_name)
            .replace(/%time%/g, event_time)
            .replace(/%info%/g, event.event_info)
            .replace(/%result%/g, event.result);

        $("#events_body").append(row);
    },

    schedule_next_update: function(data) {
        // 2-3 sec delay so that if there are multiple tabs polling the backed
        // the requests are spread in time
        var delay = 2000 + Math.floor((Math.random() * 1000) + 1);

        if (data.need_update) {
            setTimeout(function () {
                horizon.event_log.fetch_update_events();
            }, delay);
        }
    }
};
