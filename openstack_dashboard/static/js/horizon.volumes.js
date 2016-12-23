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

horizon.Volumes = {
  selected_volume_type: null,
  volume_types: [],

  initWithTypes: function(volume_types) {
    this.volume_types = volume_types;

    this._attachInputHandlers();

    this.getSelectedType();
    this.showTypeDescription();
    $("#id_volume_source_type").change(this._toggleTypeSelector);
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
    } else {
      this.toggleTypeDescription(true);
    }
  },

  toggleTypeDescription: function(hide) {
    var selected_volume_source =
          $("#id_volume_source_type").children(":selected").val();
    if(hide || selected_volume_source === 'volume_source' ||
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
  },

  _toggleTypeSelector: function() {
    // Hide the type field if the source type is snapshot
    var createFromSnapshot =
        $("#id_volume_source_type").children(":selected").val() === 'snapshot_source';
    $("#id_type").closest(".form-group").toggleClass("hidden", createFromSnapshot);
  }
};
