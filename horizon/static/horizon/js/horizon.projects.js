/* Namespace for core functionality related to Project Workflows. */
horizon.projects = {

  current_membership: [],
  users: [],
  roles: [],
  networks_selected: [],
  networks_available: [],
  has_roles: true,
  default_role_id: "",

  /* Parses the form field selector's ID to get either the
   * role or user id (i.e. returns "id12345" when
   * passed the selector with id: "id_user_id12345").
   **/
  get_field_id: function(id_string) {
    return id_string.slice(id_string.lastIndexOf("_") + 1);
  },

  /*
   * Gets the html select element associated with a given
   * role id.
   **/
  get_role_element: function(role_id) {
      return $('select[id^="id_role_' + role_id + '"]');
  },

  /*
   * Gets the html ul element associated with a given
   * user id. I.e., the user's row.
   **/
  get_user_element: function(user_id) {
      return $('li[data-user-id$=' + user_id + ']').parent();
  },

  /*

   * Gets the html select element associated with a given
   * network id for network_id.
   **/
  get_network_element: function(network_id) {
      return $('li > label[for^="id_network_' + network_id + '"]');
  },

  /*
   * Initializes all of the horizon.projects lists with
   * data parsed from the hidden form fields, as well as the
   * default role id.
   **/
  init_properties: function() {
    horizon.projects.has_roles = $(".project_membership").data('show-roles') !== "no";
    horizon.projects.default_role_id = $('#id_default_role').attr('value');
    horizon.projects.init_user_list();
    horizon.projects.init_role_list();
    horizon.projects.init_current_membership();
  },

  /*
   * Initializes an associative array mapping user ids to user names.
   **/
  init_user_list: function() {
    horizon.projects.users = [];
    _.each($(this.get_role_element("")).find("option"), function (option) {
      horizon.projects.users[option.value] = option.text;
    });
  },

  /*
   * Initializes an associative array mapping role ids to role names.
   **/
  init_role_list: function() {
    horizon.projects.roles = [];
    _.each($('label[for^="id_role_"]'), function(role) {
      var id = horizon.projects.get_field_id($(role).attr('for'));
      horizon.projects.roles[id] = $(role).text();
    });
  },

  /*
   * Initializes an associative array of lists of the current
   * members for each available role.
   **/
  init_current_membership: function() {
    horizon.projects.current_membership = [];
    var members_list = [];
    var role_name, role_id, selected_members;
    _.each(this.get_role_element(''), function(value, key) {
      role_id = horizon.projects.get_field_id($(value).attr('id'));
      role_name = $('label[for="id_role_' + role_id + '"]').text();

      // get the array of members who are selected in this list
      selected_members = $(value).find("option:selected");
      // extract the member names and add them to the dictionary of lists
      members_list = [];
      if (selected_members) {
        _.each(selected_members, function(member) {
          members_list.push(member.value);
        });
      }
      horizon.projects.current_membership[role_id] = members_list;
    });
  },

  /*
   * Initializes an associative array of lists of the current
   * networks.
   **/
  init_network_list: function() {
    horizon.projects.networks_selected = [];
    horizon.projects.networks_available = [];
    $(this.get_network_element("")).each(function(){
      var $this = $(this);
      var $input = $this.children("input");
      var network_property = {
        name:$this.text().replace(/^\s+/,""),
        id:$input.attr("id"),
        value:$input.attr("value")
      };
      if($input.is(':checked')) {
        horizon.projects.networks_selected.push(network_property);
      } else {
        horizon.projects.networks_available.push(network_property);
      }
    });
  },
  /*
   * Returns the ids of roles the user is a member of.
   **/
  get_user_roles: function(user_id) {
    var roles = [];
    for (var role in horizon.projects.current_membership) {
      if ($.inArray(user_id, horizon.projects.current_membership[role]) >= 0) {
        roles.push(role);
      }
    }
    return roles;
  },

  /*
   * Updates the selected values on the role_list's form field, as
   * well as the current_membership dictionary's list.
   **/
  update_role_lists: function(role_id, new_list) {
    this.get_role_element(role_id).val(new_list);
    horizon.projects.current_membership[role_id] = new_list;
  },

  /*
   * Helper function for remove_user_from_role.
   **/
  remove_user: function(user_id, role_id, role_list) {
    var index = role_list.indexOf(user_id);
    if (index >= 0) {
      // remove member from list
      role_list.splice(index, 1);
      horizon.projects.update_role_lists(role_id, role_list);
    }
  },

  /*
   * Searches through the role lists and removes a given user
   * from the lists.
   **/
  remove_user_from_role: function(user_id, role_id) {
    var role_list;
    if (role_id) {
      role_list = horizon.projects.current_membership[role_id];
      horizon.projects.remove_user(user_id, role_id, role_list);
    }
    else {
      // search for membership in role lists
      for (var role in horizon.projects.current_membership) {
        role_list = horizon.projects.current_membership[role];
        horizon.projects.remove_user(user_id, role, role_list);
      }
    }
  },

  /*
   * Adds a given user to a given role list.
   **/
  add_user_to_role: function(user_id, role_id) {
    var role_list = horizon.projects.current_membership[role_id];
    role_list.push(user_id);
    horizon.projects.update_role_lists(role_id, role_list);
  },

  update_user_role_dropdown: function(user_id, role_ids, user_el) {
    if (typeof(role_ids) === 'undefined') {
       role_ids = horizon.projects.get_user_roles(user_id);
    }
    if (typeof(user_el) === 'undefined') {
       user_el = horizon.projects.get_user_element(user_id);
    }

    var $dropdown = user_el.find("li.member").siblings('.dropdown');
    var $role_items = $dropdown.children('.role_dropdown').children('li');

    $role_items.each(function (idx, el) {
      if (_.contains(role_ids, $(el).data('role-id'))) {
        $(el).addClass('selected');
      } else {
        $(el).removeClass('selected');
      }
    });

    // set the selection back to default role
    var $roles_display = $dropdown.children('.dropdown-toggle').children('.roles_display');
    var roles_to_display = [];
    for (var i = 0; i < role_ids.length; i++) {
        if (i == 2) {
            roles_to_display.push('...');
            break;
        }
        roles_to_display.push(horizon.projects.roles[role_ids[i]]);
    }
    text = roles_to_display.join(', ');
    if (text.length == 0) text = 'No roles';
    $roles_display.text(text);
  },

  /*
   * Generates the HTML structure for a user that will be displayed
   * as a list item in the project member list.
   **/
  generate_user_element: function(user_name, user_id, role_ids, text) {
    var str_id = "id_user_" + user_id;

    var roles = [];
    for (var r in horizon.projects.roles) {
      var role = {};
      role['role_id'] = r;
      role['role_name'] = horizon.projects.roles[r];
      roles.push(role);
    }

    var template = horizon.templates.compiled_templates["#project_user_template"],
    params = {user_id: str_id,
              default_role: horizon.projects.roles[horizon.projects.default_role_id],
              user_name: user_name,
              text: text,
              roles: roles},
    user_el = $(template.render(params));
    this.update_user_role_dropdown(str_id, role_ids, user_el);
    return $(user_el);
  },

 /*
   * Generates the HTML structure for a network that will be displayed
   * as a list item in the project network list.
   **/
  generate_network_element: function(name, id, value) {
    var $li = $('<li>');
    $li.attr('name', value).html(name + '<em class="network_id">(' + value + ')</em><a href="#" class="btn btn-primary"></a>');
    return $li;
  },

  /*
  * Generates the HTML structure for the project membership UI.
  **/
  generate_html: function() {
    var user;
    for (user in horizon.projects.users) {
      var user_id = user;
      var user_name = horizon.projects.users[user];
      var role_ids = this.get_user_roles(user_id);
      if (role_ids.length > 0) {
        $(".project_members").append(this.generate_user_element(user_name, user_id, role_ids, "-"));
      }
      else {
        $(".available_users").append(this.generate_user_element(user_name, user_id, role_ids, "+"));
      }
    }
    horizon.projects.detect_no_results();
  },

  /*
  * Generates the HTML structure for the project Network List.
  **/
  generate_networklist_html: function() {
    var self = this;
    var updateForm = function() {
      var lists = $("#networkListId div.input li").attr('data-index',100);
      var active_networks = $("#selected_network > li").map(function(){
        return $(this).attr("name");
      });
      $("#networkListId div.input input:checkbox").removeAttr('checked');
      active_networks.each(function(index, value){
        $("#networkListId div.input input:checkbox[value=" + value + "]")
        .attr('checked','checked')
        .parents("li").attr('data-index',index);
      });
      $("#networkListId div.input ul").html(
        lists.sort(function(a,b){
          if( $(a).data("index") < $(b).data("index")) return -1;
          if( $(a).data("index") > $(b).data("index")) return 1;
          return 0;
        })
      );
    };
    $("#networkListSortContainer").show();
    $("#networkListIdContainer").hide();
    self.init_network_list();
    $.each(self.networks_available, function(index, value){
      $("#available_network").append(self.generate_network_element(value.name, value.id, value.value));
    });
    $.each(self.networks_selected, function(index, value){
      $("#selected_network").append(self.generate_network_element(value.name, value.id, value.value));
    });
    // $(".networklist > li").click(function(){
    //   $(this).toggleClass("ui-selected");
    // });
    $(".networklist > li > a.btn").click(function(e){
      var $this = $(this);
      e.preventDefault();
      e.stopPropagation();
      if($this.parents("ul#available_network").length > 0) {
        $this.parent().appendTo($("#selected_network"));
      } else if ($this.parents("ul#selected_network").length > 0) {
        $this.parent().appendTo($("#available_network"));
      }
      updateForm();
    });
    if ($("#networkListId > div.control-group.error").length > 0) {
      var errortext = $("#networkListId > div.control-group.error").find("span.help-inline").text();
      $("#selected_network_h4").before($('<div class="dynamic-error">').html(errortext));
    }
    $(".networklist").sortable({
        connectWith: "ul.networklist",
        placeholder: "ui-state-highlight",
        distance: 5,
        start:function(e,info){
          $("#selected_network").addClass("dragging");
        },
        stop:function(e,info){
          $("#selected_network").removeClass("dragging");
          updateForm();
        }
    }).disableSelection();
  },


  /*
  * Triggers on click of link to add/remove member from the project.
  **/
  update_membership: function() {
    $(".available_users, .project_members").on('click', ".btn-group a[href='#add_remove']", function (evt) {
      evt.preventDefault();
      var available = $(".available_users").has($(this)).length;
      var user_id = horizon.projects.get_field_id($(this).parent().siblings().attr('data-user-id'));
      var user_el = $(this).parent().parent();

      if (available) {
        var default_role = horizon.projects.default_role_id;
        $(this).text("-");
        $(".project_members").append(user_el);
        horizon.projects.add_user_to_role(user_id, default_role);

        if (horizon.projects.has_roles) {
          $(this).parent().siblings(".role_options").show();
          horizon.projects.update_user_role_dropdown(user_id, [default_role], user_el);
        }
      }
      else {
        $(this).text("+");
        $(this).parent().siblings(".role_options").hide();
        $(".available_users").append(user_el);
        horizon.projects.remove_user_from_role(user_id);
      }

      // update lists
      horizon.projects.list_filtering();
      horizon.projects.detect_no_results();

      // remove input filters
      $("input.filter").val("");
    });
  },

  /*
   * Detects whether each list has members and if it does not
   * displays a message to the user.
   **/
  detect_no_results: function () {
    $('.filterable').each( function () {
      var filter = $(this).find('ul').attr('class');

      if (!$('.' + filter).children('ul').length) {
        $('#no_' + filter).show();
        $("input[id='" + filter + "']").attr('disabled', 'disabled');
      }
      else {
        $('#no_' + filter).hide();
        $("input[id='" + filter + "']").removeAttr('disabled');
      }
    });
  },

  /*
  * Triggers on selection of new role for a member.
  **/
  select_member_role: function() {
    $(".available_users, .project_members").on('click', '.role_dropdown li', function (evt) {
      evt.preventDefault();
      evt.stopPropagation();

      // get the newly selected role and the member's name
      var new_role_id = $(this).attr("data-role-id");
      var id_str = $(this).parent().parent().siblings(".member").attr("data-user-id");
      var user_id = horizon.projects.get_field_id(id_str);

      // update role lists
      if ($(this).hasClass('selected')) {
        $(this).removeClass('selected');
        horizon.projects.remove_user_from_role(user_id, new_role_id);
      } else {
        $(this).addClass('selected');
        horizon.projects.add_user_to_role(user_id, new_role_id);
      }
      horizon.projects.update_user_role_dropdown(user_id);
    });
  },

  /*
   * Triggers on the addition of a new user via the inline object creation field.
   **/
  add_new_user: function() {
    $("select[id='id_new_user']").on('change', function (evt) {
      // add the user to the visible list
      var user_name = $(this).find("option").text();
      var user_id = $(this).find("option").attr("value");
      var default_role_id = horizon.projects.default_role_id;
      $(".project_members").append(horizon.projects.generate_user_element(user_name, user_id, [default_role_id], "-"));

      // add the user to the hidden role lists and the users list
      horizon.projects.users[user_id] = user_name;
      $("select[multiple='multiple']").append("<option value='" + user_id + "'>" + horizon.projects.users[user_id] + "</option>");
      horizon.projects.add_user_to_role(user_id, default_role_id);

      // remove option from hidden select
      $(this).text("");

      // reset lists and input filters
      horizon.projects.list_filtering();
      horizon.projects.detect_no_results();
      $("input.filter").val("");

      // fix styling
      $(".project_members .btn-group").removeClass('last_stripe');
      $(".project_members .btn-group:last").addClass('last_stripe');
    });
  },

  /*
   * Style the inline object creation button, hide the associated field.
   **/
  add_new_user_styling: function() {
    var add_user_el = $("label[for='id_new_user']").parent();
    $(add_user_el).find("select").hide();
    $("#add_user").append($(add_user_el));
    $(add_user_el).addClass("add_user");
    $(add_user_el).find("label, .input").addClass("add_user_btn");
  },

  /*
  * Fixes the striping of the fake table upon modification of the lists.
  **/
  fix_stripes: function() {
    $('.fake_table').each( function () {
      var filter = "." + $(this).attr('id');
      var visible = " .btn-group:visible";
      var even = " .btn-group:visible:even";
      var last = " .btn-group:visible:last";

      // fix striping of rows
      $(filter + visible).removeClass('dark_stripe');
      $(filter + visible).addClass('light_stripe');
      $(filter + even).removeClass('light_stripe');
      $(filter + even).addClass('dark_stripe');

      // fix bottom border of new last element
      $(filter + visible).removeClass('last_stripe');
      $(filter + last).addClass('last_stripe');
    });
  },

  /*
   * Sets up filtering for each list of users.
   **/
  list_filtering: function () {
    // remove previous lists' quicksearch events
    $('input.filter').unbind();

    // set up quicksearch to filter on input
    $('.filterable').each(function () {
      var filter = $(this).children().children('ul').attr('class');
      var input = $("input[id='" + filter +"']");
      input.quicksearch('ul.' + filter + ' ul li span.user_name', {
            'delay': 200,
            'loader': 'span.loading',
            'show': function () {
              $(this).parent().parent().show();
                if (filter == "available_users") {
                  $(this).parent('.dropdown-toggle').hide();
                }
              },
            'hide': function () {
              $(this).parent().parent().hide();
            },
            'noResults': 'ul#no_' + filter,
            'onAfter': function () {
                horizon.projects.fix_stripes();
            },
            'prepareQuery': function (val) {
              return new RegExp(val, "i");
            },
            'testQuery': function (query, txt, span) {
              if ($(input).attr('id') == filter) {
                $(input).prev().removeAttr('disabled');
                return query.test($(span).text());
              }
              else
                return true;
            }
      });
    });
  },

  /*
   * Calls set-up functions upon loading the workflow.
   **/
  workflow_init: function(modal) {
    horizon.projects.generate_networklist_html();

    // fix the dropdown menu overflow issues
    $(".tab-content, .workflow").addClass("dropdown_fix");

    $(modal).find('form').each( function () {
        var $form = $(this);

        // Do nothing if this isn't a membership modal
        if ($form.find('div.project_membership').length == 0) {
           return; // continue
        }

        // call the initalization functions
        horizon.projects.init_properties();
        horizon.projects.generate_html();
        horizon.projects.update_membership();
        horizon.projects.select_member_role();
        horizon.projects.add_new_user();

        // initially hide role dropdowns for available users list
        $form.find(".available_users .role_options").hide();

        // hide the dropdown for members too if we don't need to show it
        if (!horizon.projects.has_roles) {
          $form.find(".project_members .role_options").hide();
        }

        // unfocus filter fields
        $form.find("#update_project__update_members input").blur();

        // prevent filter inputs from submitting form on 'enter'
        $form.find('.project_membership').keydown(function(event){
          if(event.keyCode == 13) {
            event.preventDefault();
            return false;
          }
        });

        // add filtering + styling to the inline obj creation btn
        horizon.projects.add_new_user_styling();
        horizon.projects.list_filtering();
        horizon.projects.detect_no_results();

        // fix initial striping of rows
        $form.find('.fake_table').each( function () {
          var filter = "." + $(this).attr('id');
          $(filter + ' .btn-group:even').addClass('dark_stripe');
          $(filter + ' .btn-group:last').addClass('last_stripe');
        });
    });
  }
};


horizon.addInitFunction(function() {
  horizon.modals.addModalInitFunction(horizon.projects.workflow_init);
});
