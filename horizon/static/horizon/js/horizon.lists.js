horizon.lists = {

  /*
   * Generates the HTML structure for a "+type+" that will be displayed
   * as a list item.
   **/
  generate_element: function (name, value, type) {
    var $li = $('<li>');
    $li.attr('name', value).html(
      name + '<em class="' + type + '_id">(' + value + ')</em>' +
      '<a href="#" class="btn btn-primary"></a>'
    );
    return $li;
  },

  /*
   * Generates the HTML structure for the feature list.
   **/
  generate_html: function (type) {
    var self = this;
    self.feature_type = type;

    var update_form = function () {
      var lists = $("#"+type+"ListId li").attr('data-index',100);
      var active_features = $("#selected_"+type+" > li").map(function () {
        return $(this).attr("name");
      });
      $("#"+type+"ListId input:checkbox").removeAttr('checked');
      active_features.each(function (index, value) {
        $("#"+type+"ListId input:checkbox[value=" + value + "]")
          .prop('checked', true)
          .parents("li").attr('data-index',index);
      });
      $("#"+type+"ListId ul").html(
        lists.sort(function (a,b) {
          if($(a).data("index") < $(b).data("index")) { return -1; }
          if($(a).data("index") > $(b).data("index")) { return 1; }
          return 0;
        })
      );
    };

    var append_new_elements = function (type, state) {
      $("#"+state+"_"+type).empty();
      $.each(self[type+"s_"+state], function (index, value) {
        $("#"+state+"_"+self.feature_type).append(
          self.generate_element(value.name, value.value, self.feature_type)
        );
      });
    };

    $("#"+type+"ListSortContainer").show();
    $("#"+type+"ListIdContainer").hide();
    self.init_list(type);
    append_new_elements(type, "available");
    append_new_elements(type, "selected");

    $("."+type+"list > li > a.btn").click(function (e) {
      var $this = $(this);
      e.preventDefault();
      e.stopPropagation();

      if($this.parents("ul#available_"+type).length > 0) {
        $this.parent().appendTo($("#selected_"+type));
      } else if ($this.parents("ul#selected_"+type).length > 0) {
        $this.parent().appendTo($("#available_"+type));
      }
      update_form();
    });

    if ($("#"+type+"ListId > div.form-group.error").length > 0) {
      var errortext = $("#"+type+"ListId > div.form-group.error").find("span.help-block").text();
      $("#selected_"+type+"_label").before($('<div class="dynamic-error">').html(errortext));
    }

    $("."+type+"list").sortable({
      connectWith: "ul."+type+"list",
      placeholder: "ui-state-highlight",
      distance: 5,
      start:function () {
        $("#selected_"+type).addClass("dragging");
      },
      stop:function () {
        $("#selected_"+type).removeClass("dragging");
        update_form();
      }
    }).disableSelection();
  },

  get_console_log: function (via_user_submit, user_decided_length) {
    var form_element = $("#tail_length");
    var error_txt = gettext('There was a problem communicating with the server, please try again.');

    if (!via_user_submit) {
      via_user_submit = false;
    }

    $.ajax({
      url: $(form_element).attr('action'),
      data: (user_decided_length) ? $(form_element).serialize() : "length=35",
      method: 'get',
      success: function (response_body) {
        $('pre.logs').text(response_body);
      },
      error: function () {
        if(via_user_submit) {
          horizon.clearErrorMessages();
          horizon.toast.add('error', error_txt);
        }
      }
    });
  },

  /*
   * Gets the html select element associated with a given id.
   **/
  get_element: function (id, type) {
    return $('label[for^="id_'+type+'_' + id + '"]');
  },

  /*
   * Initializes an associative array of lists for the current feature.
   **/
  init_list: function (type) {
    var self = this;
    self[type+"s_selected"] = [];
    self[type+"s_available"] = [];

    $(horizon.lists.get_element("", type)).each(function () {
      var $parent = $(this).parent();
      var $input = $parent.children("input");
      var name = horizon.string.escapeHtml($parent.text().replace(/^\s+/, ""));
      var properties = {
        "name": name,
        "id": $input.attr("id"),
        "value": $input.attr("value")
      };

      var feature_state = ($input.is(":checked")) ? "selected" : "available";
      self[type+"s_"+feature_state].push(properties);
    });
  }

};
