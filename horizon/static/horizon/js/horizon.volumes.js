
horizon.Volumes = {
  selected_volume_type: null,
  volume_types: [],

  initWithTypes: function(volume_types) {
    this.volume_types = volume_types;

    this._attachInputHandlers();

    this.getSelectedType();
    this.showTypeDescription();
  },

  /*
   *Returns the type object for the selected type in the form.
   */
  getSelectedType: function() {

    this.selected_volume_type = $.grep(this.volume_types, function(type) {
        var selected_name = $("#id_type").children(":selected").val();
        return type.name === selected_name;
      })[0];

    return this.selected_volume_type;
  },

  showTypeDescription: function() {
    this.getSelectedType();

    if (this.selected_volume_type) {
      var description = this.selected_volume_type.description;
      var name = this.selected_volume_type.name;
      $("#id_show_volume_type_name").html(name);

      if (description) {
          $("#id_show_volume_type_desc").html(description);
      } else {
          $("#id_show_volume_type_desc").html(
              gettext('No description available.'));
      }
    }
  },

  toggleTypeDescription: function() {
    var selected_volume_source =
          $("#id_volume_source_type").children(":selected").val();
    if(selected_volume_source === 'volume_source' ||
       selected_volume_source === 'snapshot_source') {
      $("#id_show_volume_type_desc_div").hide();
    }
    else {
      $("#id_show_volume_type_desc_div").show();
    }
  },

  _attachInputHandlers: function() {
    var scope = this;

    var eventCallback_type = function() {
        scope.showTypeDescription();
    };

    $('#id_type').on('change', eventCallback_type);

    var eventCallback_volume_source_type = function() {
        scope.toggleTypeDescription();
    };

    $('#id_volume_source_type').on('change', eventCallback_volume_source_type);
  }
};
