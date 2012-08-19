/* Namespace for core functionality related to Project Workflows. */
horizon.projects = {

  current_membership: [],
  users: [],
  roles: [],
  default_role_id: "",
  workflow_loaded: false,
  no_project_members: gettext('This project currently has no members.'),
  no_available_users: gettext('No more available users to add.'),
  no_filter_results: gettext('No users found.'),
  filter_btn_text: gettext('Filter'),

  /* Parses the form field selector's ID to get either the
   * role or user id (i.e. returns "id12345" when
   * passed the selector with id: "id_user_id12345").
   **/
  get_field_id: function(id_string) {
    return id_string.slice(id_string.lastIndexOf("_") + 1);
  },

  /*
   * Gets the html select element associated with a given
   * role id for role_id.
   **/
  get_role_element: function(role_id) {
      return $('select[id^="id_role_' + role_id + '"]');
  },

  /*
   * Initializes all of the horizon.projects lists with
   * data parsed from the hidden form fields, as well as the
   * default role id.
   **/
  init_properties: function() {
    horizon.projects.default_role_id = $('#id_default_role').attr('value');
    horizon.projects.init_user_list();
    horizon.projects.init_role_list();
    horizon.projects.init_current_membership();
  },

  /*
   * Initializes an associative array mapping user ids to user names.
   **/
  init_user_list: function() {
    _.each($(this.get_role_element("")).find("option"), function (option) {
      horizon.projects.users[option.value] = option.text;
    });
  },

  /*
   * Initializes an associative array mapping role ids to role names.
   **/
  init_role_list: function() {
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
   * Checks to see whether a user is a member of the current project.
   * If they are, returns the id of their primary role.
   **/
  is_project_member: function(user_id) {
    for (var role in horizon.projects.current_membership) {
      if ($.inArray(user_id, horizon.projects.current_membership[role]) >= 0) {
        return role;
      }
    }
    return false;
  },

  /*
   * Updates the selected values on the role_list's form field, as
   * well as the current_membership dictionary's list.
   **/
  update_role_lists: function(role_id, new_list) {
    this.get_role_element(role_id).val(new_list);
    this.get_role_element(role_id).find("option[value='" + role_id + "").attr("selected", "selected");

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

  /*
   * Generates the HTML structure for a user that will be displayed
   * as a list item in the project member list.
   **/
  generate_user_element: function(user_name, user_id, text) {
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
    return $(user_el);
  },

  set_selected_role: function(selected_el, role_id) {
    $(selected_el).text(horizon.projects.roles[role_id]);
    $(selected_el).attr('data-role-id', role_id);
  },

  /*
  * Generates the HTML structure for the project membership UI.
  **/
  generate_html: function() {
    var user;
    for (user in horizon.projects.users) {
      var user_id = user;
      var user_name = horizon.projects.users[user];
      var role_id = this.is_project_member(user_id);
      if (role_id) {
        $(".project_members").append(this.generate_user_element(user_name, user_id, "-"));
          var $selected_role = $("li[data-user-id$='" + user_id + "']").siblings('.dropdown').children('.dropdown-toggle').children('span');
          horizon.projects.set_selected_role($selected_role, role_id);
      }
      else {
        $(".available_users").append(this.generate_user_element(user_name, user_id, "+"));
      }
    }
    horizon.projects.detect_no_results();
  },

  /*
  * Triggers on click of link to add/remove member from the project.
  **/
  update_membership: function() {
    $(".available_users, .project_members").on('click', ".btn-group a[href='#add_remove']", function (evt) {
      var available = $(".available_users").has($(this)).length;
      var user_id = horizon.projects.get_field_id($(this).parent().siblings().attr('data-user-id'));

      if (available) {
        $(this).text("-");
        $(this).parent().siblings(".role_options").show();
        $(".project_members").append($(this).parent().parent());

        horizon.projects.add_user_to_role(user_id, horizon.projects.default_role_id);
      }
      else {
        $(this).text("+");
        $(this).parent().siblings(".role_options").hide();
        $(".available_users").append($(this).parent().parent());

        horizon.projects.remove_user_from_role(user_id);

        // set the selection back to default role
        var $selected_role = $(this).parent().siblings('.dropdown').children('.dropdown-toggle').children('.selected_role');
        horizon.projects.set_selected_role($selected_role, horizon.projects.default_role_id);
      }

      // update lists
      horizon.projects.list_filtering();
      horizon.projects.detect_no_results();

      // remove input filters
      $("input.filter").val(horizon.projects.filter_btn_text);
    });
  },

  /*
   * Detects whether each list has members and if it does not
   * displays a message to the user.
   **/
  detect_no_results: function () {
    $('.filterable').each( function () {
      var filter = $(this).find('ul').attr('class'),
          text;
      if (filter == 'project_members')
        text = horizon.projects.no_project_members;
      else
        text = horizon.projects.no_available_users;

      if (!$('.' + filter).children('ul').length) {
        $('#no_' + filter).text(text);
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
      var $selected_el = $(this).parent().prev().children('.selected_role');
      $selected_el.text($(this).text());

      // get the newly selected role and the member's name
      var new_role_id = $(this).attr("data-role-id");
      var id_str = $(this).parent().parent().siblings(".member").attr("data-user-id");
      var user_id = horizon.projects.get_field_id(id_str);

      // update role lists
      horizon.projects.remove_user_from_role(user_id, $selected_el.attr('data-role-id'));
      horizon.projects.add_user_to_role(user_id, new_role_id);
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
      $(".project_members").append(horizon.projects.generate_user_element(user_name, user_id, "-"));

      // add the user to the hidden role lists and the users list
      horizon.projects.users[user_id] = user_name;
      $("select[multiple='multiple']").append("<option value='" + user_id + "'>" + horizon.projects.users[user_id] + "</option>");
      horizon.projects.add_user_to_role(user_id, horizon.projects.default_role_id);

      // remove option from hidden select
      $(this).text("");

      // reset lists and input filters
      horizon.projects.list_filtering();
      horizon.projects.detect_no_results();
      $("input.filter").val(horizon.projects.filter_btn_text);

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

    // set up what happens on focus of input boxes
    $("input.filter").on('focus', function() {
      if ($(this).val() === horizon.projects.filter_btn_text) {
        $(this).val("");
      }
    });

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
            'onBefore': function () {
              $('ul#no_' + filter).text(horizon.projects.no_filter_results);
            },
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
    if (!horizon.projects.workflow_loaded) {
      $(modal).find('form').each( function () {
        // call the initalization functions
        horizon.projects.init_properties();
        horizon.projects.generate_html();
        horizon.projects.update_membership();
        horizon.projects.select_member_role();
        horizon.projects.add_new_user();

        // initially hide role dropdowns for available users list
        $(".available_users .role_options").hide();

        // fix the dropdown menu overflow issues
        $(".tab-content, .workflow").addClass("dropdown_fix");

        // unfocus filter fields
        $("#update_project__update_members input").blur();

        // prevent filter inputs from submitting form on 'enter'
        $('.project_membership').keydown(function(event){
          if(event.keyCode == 13) {
            event.preventDefault();
            return false;
          }
        });

        // add filtering + styling to the inline obj creation btn
        horizon.projects.add_new_user_styling();
        horizon.projects.list_filtering();
        horizon.projects.detect_no_results();
        horizon.projects.workflow_loaded = true;

        // fix initial striping of rows
        $('.fake_table').each( function () {
          var filter = "." + $(this).attr('id');
          $(filter + ' .btn-group:even').addClass('dark_stripe');
          $(filter + ' .btn-group:last').addClass('last_stripe');
        });
      });
    }
  }
};

horizon.addInitFunction(function() {
  $('.btn').on('click', function (evt) {
    horizon.projects.workflow_loaded = false;
  });
  horizon.modals.addModalInitFunction(horizon.projects.workflow_init);
});
