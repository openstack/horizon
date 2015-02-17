/* Namespace for core functionality related to Membership Workflow Step. */
horizon.membership = {

  current_membership: [],
  data: [],
  roles: [],
  has_roles: [],
  default_role_id: [],
  app_names: [],

  /* Parses the form field selector's ID to get either the
   * role or user id (i.e. returns "id12345" when
   * passed the selector with id: "id_group_id12345").
   **/
  get_field_id: function(id_string) {
    return id_string.slice(id_string.lastIndexOf("_") + 1);
  },

  /*
   * Gets the html select element associated with a given
   * role id.
   **/
  get_role_element: function(step_slug, role_id) {
    return $('select[id^="id_' + step_slug + '_role_' + role_id + '"]');
  },

  /*
   * Gets the html ul element associated with a given
   * data id. I.e., the member's row.
   **/
  get_member_element: function(step_slug, data_id) {
    return $('div[data-' + step_slug + '-id$=' + data_id + ']').parent();
  },

  /*
   * Initializes all of the horizon.membership lists with
   * data parsed from the hidden form fields, as well as the
   * default role id.
   **/
  init_properties: function(step_slug) {
    horizon.membership.has_roles[step_slug] = $("." + step_slug + "_membership").data('show-roles') !== "False";
    horizon.membership.default_role_id[step_slug] = $('#id_default_' + step_slug + '_role').attr('value');
    horizon.membership.init_data_list(step_slug);
    horizon.membership.init_role_list(step_slug);
    horizon.membership.init_current_membership(step_slug);
  },

  /*
   * Initializes an associative array mapping data ids to display names.
   **/
  init_data_list: function(step_slug) {
    horizon.membership.data[step_slug] = [];
    angular.forEach($(this.get_role_element(step_slug, "")).find("option"), function (option) {
      horizon.membership.data[step_slug][option.value] = option.text;
    });
  },

  /*
   * Initializes an associative array mapping role ids to role names.
   **/
  init_role_list: function(step_slug) {
    horizon.membership.roles[step_slug] = [];
    angular.forEach($('label[for^="id_' + step_slug + '_role_"]'), function(role) {
      var input_name = $(role).attr('for')
      var id = horizon.membership.get_field_id(input_name);
      var app_id = $('#' + input_name).attr('data-superset-id')

      // store name for rendering purposes
      horizon.membership.app_names[app_id] = $('#' + input_name).attr('data-superset-name')
      
      if (!horizon.membership.roles[step_slug][app_id]){
        // init the second dimension of the array if not created
        horizon.membership.roles[step_slug][app_id] = []
      }
      horizon.membership.roles[step_slug][app_id][id] = $(role).text();
    });
  },

  /*
   * Initializes an associative array of lists of the current
   * members for each available role.
   **/
  init_current_membership: function(step_slug) {
    horizon.membership.current_membership[step_slug] = [];
    var members_list = [];
    var role_name, role_id, selected_members;
    angular.forEach(this.get_role_element(step_slug, ''), function(value, key) {
      role_id = horizon.membership.get_field_id($(value).attr('id'));
      role_name = $('label[for="id_' + step_slug + '_role_' + role_id + '"]').text();

      // get the array of members who are selected in this list
      selected_members = $(value).find("option:selected");
      // extract the member names and add them to the dictionary of lists
      members_list = [];
      if (selected_members) {
        angular.forEach(selected_members, function(member) {
          members_list.push(member.value);
        });
      }
      horizon.membership.current_membership[step_slug][role_id] = members_list;
    });
  },

  /*
   * Returns the ids of roles the data is member of.
   **/
  get_member_roles: function(step_slug, data_id) {
    var roles = [];
    for (var role in horizon.membership.current_membership[step_slug]) {
      if ($.inArray(data_id, horizon.membership.current_membership[step_slug][role]) !== -1) {
        roles.push(role);
      }
    }
    return roles;
  },

  /*
   * Updates the selected values on the role_list's form field, as
   * well as the current_membership dictionary's list.
   **/
  update_role_lists: function(step_slug, role_id, new_list) {
    this.get_role_element(step_slug, role_id).val(new_list);
    horizon.membership.current_membership[step_slug][role_id] = new_list;
  },

  /*
   * Helper function for remove_member_from_role.
   **/
  remove_member: function(step_slug, data_id, role_id, role_list) {
    var index = role_list.indexOf(data_id);
    if (index >= 0) {
      // remove member from list
      role_list.splice(index, 1);
      horizon.membership.update_role_lists(step_slug, role_id, role_list);
    }
  },

  /*
   * Searches through the role lists and removes a given member
   * from the lists.
   **/
  remove_member_from_role: function(step_slug, data_id, role_id) {
    var role, membership = horizon.membership.current_membership[step_slug];
    if (role_id) {
      horizon.membership.remove_member(
        step_slug, data_id, role_id, membership[role_id]
      );
    }
    else {
      // search for membership in role lists
      for (role in membership) {
        if (membership.hasOwnProperty(role)) {
          horizon.membership.remove_member(
            step_slug, data_id, role,  membership[role]
          );
        }
      }
    }
  },

  /*
   * Adds a member to a given role list.
   **/
  add_member_to_role: function(step_slug, data_id, role_id) {
    var role_list = horizon.membership.current_membership[step_slug][role_id];
    role_list.push(data_id);
    horizon.membership.update_role_lists(step_slug, role_id, role_list);
  },

  update_member_role_dropdown: function(step_slug, data_id, role_ids, member_el) {
    if (typeof(role_ids) === 'undefined') {
      role_ids = horizon.membership.get_member_roles(step_slug, data_id);
    }
    if (typeof(member_el) === 'undefined') {
      member_el = horizon.membership.get_member_element(step_slug, data_id);
    }

    var $dropdown = member_el.find("div.member").siblings('.dropdown');
    var $role_items = $dropdown.children('.role_dropdown').find('li.role_dropdown_role');
    $role_items.each(function (idx, el) {
      if ($.inArray(($(el).data('role-id')), role_ids) !== -1) {
        $(el).addClass('active');
      } else {
        $(el).removeClass('active');
      }
    });

    var $roles_display = $dropdown.children('.dropdown-toggle').children('.roles_display');
    text = role_ids.length > 0 ? role_ids.length + " roles" : "No roles";
    $roles_display.text(text);
  },

  /*
   * Generates the HTML structure for a member that will be displayed
   * as a list item in the member list.
   **/
  generate_member_element: function(step_slug, display_name, data_id, role_ids, update_icon) {
    var apps = [],
      that = this,
      membership_roles = that.roles[step_slug],
      r;
    for (app in membership_roles){
      var roles = []
      for (r in membership_roles[app]) {
        if (membership_roles[app].hasOwnProperty(r)){
          roles.push({
            role_id: r,
            role_name: membership_roles[app][r],
          });
        }
      }
      apps.push({
        app_name: horizon.membership.app_names[app],
        roles: roles,
      })
    }

    var template = horizon.templates.compiled_templates["#membership_template"],
      params = {
        data_id: "id_" + step_slug + "_" + data_id,
        step_slug: step_slug,
        display_name: display_name,
        apps: apps,
        roles_label: gettext("Roles"),
        update_icon: update_icon,
      },
      member_el = $(template.render(params));
    this.update_member_role_dropdown(step_slug, params.data_id, role_ids, member_el);
    return $(member_el);
  },

  /*
   * Generates the HTML structure for the membership UI.
   **/
  generate_html: function(step_slug) {
    var data_id, data = horizon.membership.data[step_slug];
    for (data_id in data) {
      if(data.hasOwnProperty(data_id)){
        var display_name = data[data_id];
        var role_ids = this.get_member_roles(step_slug, data_id);
        if (role_ids.length > 0) {
          $("." + step_slug + "_members").append(this.generate_member_element(step_slug, display_name, data_id, role_ids, 'fa fa-close'));
        }
        else {
          $(".available_" + step_slug).append(this.generate_member_element(step_slug, display_name, data_id, role_ids, 'fa fa-plus'));
        }
      }
    }
    horizon.membership.detect_no_results(step_slug);
  },

  /*
   * Triggers on click of link to add/remove membership association.
   **/
  update_membership: function(step_slug) {
    $(".available_" + step_slug + ", ." + step_slug + "_members").on('click', "a[href='#add_remove']", function (evt) {
      evt.preventDefault();
      var available = $(".available_" + step_slug).has($(this)).length;
      var data_id = horizon.membership.get_field_id($(this).parent().parent().attr('data-' + step_slug +  '-id'));
      var member_el = $(this).parent().parent().parent();
      if (available) {
        var default_role = horizon.membership.default_role_id[step_slug];
        $(this).removeClass( "fa-plus" ).addClass( "fa-close" );
        $("." + step_slug + "_members").append(member_el);
        if (default_role) {
          horizon.membership.add_member_to_role(step_slug, data_id, default_role);
        }

        if (horizon.membership.has_roles[step_slug]) {
          $(this).parent().parent().siblings(".role_options").show();
          var role_ids = default_role ? [default_role] : []
          horizon.membership.update_member_role_dropdown(step_slug, data_id, role_ids, member_el);
        }
      }
      else {
        $(this).removeClass( "fa-close" ).addClass( "fa-plus" );
        $(this).parent().parent().siblings(".role_options").hide();
        $(".available_" + step_slug).append(member_el);
        horizon.membership.remove_member_from_role(step_slug, data_id);
      }

      // update lists
      horizon.membership.list_filtering(step_slug);
      horizon.membership.detect_no_results(step_slug);

      // remove input filters
      $("input." + step_slug + "_filter").val("");
    });
  },

  /*
   * Detects whether each list has members and if it does not
   * displays a message to the user.
   **/
  detect_no_results: function (step_slug) {
    $('.' + step_slug +  '_filterable').each( function () {
      var css_class = $(this).find('ul').attr('class');
      // Example value: members step_slug_members
      // Pick the class name that contains the step_slug
      var filter = $.grep(css_class.split(' '), function(val){ return val.indexOf(step_slug) !== -1; })[0];

      if (!$('.' + filter).children('li').length) {
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
  select_member_role: function(step_slug) {
    $(".available_" + step_slug + ", ." + step_slug + "_members").on('click', '.role_dropdown li', function (evt) {
      evt.preventDefault();
      evt.stopPropagation();
      // get the newly selected role and the member's name
      var new_role_id = $(this).attr("data-role-id");
      if (!new_role_id) {
        // this is a application name li item, do nothing
        return
      }
      var id_str = $(this).parentsUntil( $("li.list-group-item"), "div").siblings(".member").attr("data-" + step_slug + "-id");
      var data_id = horizon.membership.get_field_id(id_str);
      // update role lists
      if ($(this).hasClass('active')) {
        $(this).removeClass('active');
        horizon.membership.remove_member_from_role(step_slug, data_id, new_role_id);
      } else {
        $(this).addClass('active');
        horizon.membership.add_member_to_role(step_slug, data_id, new_role_id);
      }
      horizon.membership.update_member_role_dropdown(step_slug, data_id);
    });
  },

  /*
   * Sets up filtering for each list of data.
   **/
  list_filtering: function (step_slug) {
    // remove previous lists' quicksearch events
    $('input.' + step_slug + '_filter').unbind();
    // set up quicksearch to filter on input
    $('.' + step_slug + '_filterable').each(function () {
      var css_class = $(this).children('ul').attr('class');
      // Example value: members step_slug_members
      // Pick the class name that contains the step_slug
      var filter = $.grep(css_class.split(' '), function(val){ return val.indexOf(step_slug) !== -1; })[0];
      var input = $("input[id='" + filter +"']");
      input.quicksearch('ul.' + filter + ' ul li span.name', {
        'delay': 200,
        'loader': 'span.loading',
        'show': function () {
          $(this).parent().parent().show();
          if (filter === "available_" + step_slug) {
            $(this).parent('.dropdown-toggle').hide();
          }
        },
        'hide': function () {
          $(this).parent().parent().hide();
        },
        'noResults': 'ul#no_' + filter,
        'onAfter': function () {
          //horizon.membership.fix_stripes(step_slug);
        },
        'prepareQuery': function (val) {
          return new RegExp(val, "i");
        },
        'testQuery': function (query, txt, span) {
          if ($(input).attr('id') === filter) {
            $(input).prev().removeAttr('disabled');
            return query.test($(span).text());
          } else {
            return true;
          }
        }
      });
    });
  },

  /*
   * Calls set-up functions upon loading the workflow.
   **/
  workflow_init: function(modal, step_slug, step_id) {
    $(modal).find('form').each( function () {
      var $form = $(this);

      // Do nothing if this isn't a membership modal
      if ($form.find('div.' + step_slug + '_membership').length === 0) {
        return; // continue
      }
      // call the initialization functions
      horizon.membership.init_properties(step_slug);
      horizon.membership.generate_html(step_slug);
      horizon.membership.update_membership(step_slug);
      horizon.membership.select_member_role(step_slug);
      //horizon.membership.add_new_member(step_slug);

      // initially hide role dropdowns for available member list
      $form.find(".available_" +  step_slug + " .role_options").hide();

      // hide the dropdown for members too if we don't need to show it
      if (!horizon.membership.has_roles[step_slug]) {
        $form.find("." + step_slug + "_members .role_options").hide();
      }
      // unfocus filter fields
      if (step_id.indexOf('update') === 0) {
        $form.find("#" + step_id + " input").blur();
      }
      // prevent filter inputs from submitting form on 'enter'
      $form.find('.' + step_slug + '_membership').keydown(function(event){
        if(event.keyCode === 13) {
          event.preventDefault();
          return false;
        }
      });

      // add filtering + styling to the inline obj creation btn
      //horizon.membership.add_new_member_styling(step_slug);
      horizon.membership.list_filtering(step_slug);
      horizon.membership.detect_no_results(step_slug);

      // fix initial striping of rows
      /*$form.find('.fake_' + step_slug + '_table').each( function () {
        var filter = "." + $(this).attr('id');
        $(filter + ' .btn-group:even').addClass('dark_stripe');
        $(filter + ' .btn-group:last').addClass('last_stripe');
      });*/
    });
  }
};
