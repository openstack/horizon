horizon.job_interface_arguments = {

    argument_template: '' +
        '<div id_attr="$id">' +
            '<table class="argument-form table table-striped table-hover" id_attr="$id">' +
                '<tr>' +
                    '<td class="col-sm-2 small-padding">' +
                        '<input type="button" class="btn btn-danger" id="delete_btn_$id" data-toggle="dropdown" onclick="horizon.job_interface_arguments.delete_interface_argument(this)" value="' + gettext('Remove') + '" />' +
                    '</td>' +
                    '<td class="col-sm-2 small-padding">' +
                        '<input id="argument_id_$id" value="$id" type="hidden" name="argument_id_$id">' +
                        '<label for="argument_name_$id">' + gettext("Name") + ':</label>' +
                    '</td>' +
                    '<td class="col-sm-4 small-padding">' +
                        '<input id="argument_name_$id" value="$name" type="text" name="argument_name_$id" class="form-control">' +
                    '</td>' +
                '</tr>' +
                '<tr>' +
                    '<td class="col-sm-2 small-padding"></td>' +
                    '<td class="col-sm-2 small-padding">' +
                        '<label for="argument_description_$id">' + gettext("Description") + ':</label>' +
                    '</td>' +
                    '<td class="col-sm-4 small-padding">' +
                        '<input id="argument_description_$id" value="$description" type="text" name="argument_description_$id" class="form-control">' +
                    '</td>' +
                '</tr>' +
                '<tr>' +
                    '<td class="col-sm-2 small-padding"></td>' +
                    '<td class="col-sm-2 small-padding">' +
                        '<label for="argument_mapping_type_$id">' + gettext("Mapping Type") + ':</label>' +
                        '<span class="help-icon" title="" data-placement="top" data-toggle="tooltip" data-original-title="' + gettext("See http://docs.openstack.org/developer/sahara/userdoc/edp.html for definitions.") + '">' +
                            '<span class="fa fa-question-circle"></span>' +
                        '</span>' +
                    '</td>' +
                    '<td class="col-sm-4 small-padding">' +
                        '<select id="argument_mapping_type_$id" selected="$mapping_type" name="argument_mapping_type_$id" class="form-control">' +
                            '<option value="args">' + gettext("Positional Argument") + '</option>' +
                            '<option value="params">' + gettext("Named Parameter") + '</option>' +
                            '<option value="configs">' + gettext("Configuration Value") + '</option>' +
                        '</select>' +
                    '</td>' +
                '</tr>' +
                '<tr>' +
                    '<td class="col-sm-2 small-padding"></td>' +
                    '<td class="col-sm-2 small-padding">' +
                        '<label for="argument_location_$id">' + gettext("Location") + ':</label>' +
                        '<span class="help-icon" title="" data-placement="top" data-toggle="tooltip" data-original-title="' + gettext("For configs and params, type the key name; for args, type the index as an integer, starting from 0.") + '">' +
                            '<span class="fa fa-question-circle"></span>' +
                        '</span>' +
                    '</td>' +
                    '<td class="col-sm-4 small-padding">' +
                        '<input id="argument_location_$id" value="$location" type="text" name="argument_location_$id" class="form-control">' +
                    '</td>' +
                '</tr>' +
                '<tr>' +
                    '<td class="col-sm-2 small-padding"></td>' +
                    '<td class="col-sm-2 small-padding">' +
                        '<label for="argument_value_type_$id">' + gettext("Value Type") + ':</label>' +
                    '</td>' +
                    '<td class="col-sm-4 small-padding">' +
                        '<select id="argument_value_type_$id" selected="$value_type" name="argument_value_type_$id" class="form-control">' +
                            '<option value="string">' + gettext("String") + '</option>' +
                            '<option value="number">' + gettext("Number") + '</option>' +
                            '<option value="data_source">' + gettext("Data Source") + '</option>' +
                        '</select>' +
                    '</td>' +
                '</tr>' +
                '<tr>' +
                    '<td class="col-sm-2 small-padding"></td>' +
                    '<td class="col-sm-2 small-padding">' +
                        '<label for="argument_required_$id">' + gettext("Required?") + ':</label>' +
                    '</td>' +
                    '<td class="col-sm-4 small-padding">' +
                        '<input id="argument_required_$id" type="checkbox" name="argument_required_$id" checked class="form-control">' +
                    '</td>' +
                '</tr>' +
                '<tr>' +
                    '<td class="col-sm-2 small-padding"></td>' +
                    '<td class="col-sm-2 small-padding">' +
                        '<label for="argument_default_value_$id">' + gettext("Default Value") + ':</label>' +
                        '<span class="help-icon" title="" data-placement="top" data-toggle="tooltip" data-original-title="' + gettext("For data sources, use a data source UUID or a path (as per data source creation.)") + '">' +
                            '<span class="fa fa-question-circle"></span>' +
                        '</span>' +
                    '</td>' +
                    '<td class="col-sm-4 small-padding">' +
                        '<input id="argument_default_value_$id" value="$default_value" type="text" name="argument_default_value_$id" class="form-control">' +
                    '</td>' +
                '</tr>' +
            '</table>' +
        '</div>',

    job_interface: null,
    argument_ids: null,
    value_type: null,
    add_argument_button: null,
    value_type_default: null,

    current_value_type: function() {
        return this.value_type.find("option:selected").html();
    },

    mark_argument_element_as_wrong: function(id) {
        $("#" + id).addClass("error");
    },

    get_next_argument_id: function() {
        var max = -1;
        $(".argument-form").each(function () {
            max = Math.max(max, parseInt($(this).attr("id_attr")));
        });
        return max + 1;
    },

    set_argument_ids: function() {
        var ids = [];
        $(".argument-form").each(function () {
            var id = parseInt($(this).attr("id_attr"));
            if (!isNaN(id)) {
                ids.push(id);
            }
        });
        this.argument_ids.val(JSON.stringify(ids));
    },

    add_argument_node: function(id, name, description, mapping_type, location, value_type, required, default_value) {
        var tmp = this.argument_template.
                replace(/\$id/g, id).
                replace(/\$name/g, name).
                replace(/\$description/g, description).
                replace(/\$mapping_type/g, mapping_type).
                replace(/\$location/g, location).
                replace(/\$value_type/g, value_type).
                replace(/\$required/g, required).
                replace(/\$default_value/g, default_value);
        this.job_interface.find("div:last").after(tmp);
        this.job_interface.show();
        this.set_argument_ids();
    },

    add_interface_argument: function() {
        var value_type = this.current_value_type();
        if (value_type === this.value_type_default) {
            return;
        }
        this.add_argument_node(this.get_next_argument_id(), "", "", "args", "", value_type, true, "");
        $(".count-field").change();
    },

    delete_interface_argument: function(el) {
        $(el).closest("div").remove();
        var id = this.get_next_argument_id();
        if (id === 0) {
            this.job_interface.hide();
        }
        this.set_argument_ids();
    },

    init_arguments: function() {
        // This line enables tooltips on this tab to properly display their help text.
        $("body").tooltip({selector: ".help-icon"});
        this.job_interface = $("#job_interface_arguments");
        this.argument_ids = $("#argument_ids");
        this.value_type = $("#value_type");
        this.add_argument_button = $("#add_argument_button");
        this.value_type_default = this.current_value_type();
        this.value_type.change(function () {
            if (horizon.job_interface_arguments.current_value_type() === this.value_type_default) {
                horizon.job_interface_arguments.add_argument_button.addClass("disabled");
            } else {
                horizon.job_interface_arguments.add_argument_button.removeClass("disabled");
            }
        });
        this.job_interface.hide();
    }
};
