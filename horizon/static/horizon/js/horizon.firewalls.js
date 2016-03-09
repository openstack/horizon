horizon.firewalls = {
  user_decided_length: false,
  rules_selected: [],
  rules_available: [],
  routers_selected: [],
  routers_available: [],

  getConsoleLog: function(via_user_submit) {
    var form_element = $("#tail_length"),
      data;

    if (!via_user_submit) {
      via_user_submit = false;
    }

    if(this.user_decided_length) {
      data = $(form_element).serialize();
    } else {
      data = "length=35";
    }

    $.ajax({
      url: $(form_element).attr('action'),
      data: data,
      method: 'get',
      success: function(response_body) {
        $('pre.logs').text(response_body);
      },
      error: function() {
        if(via_user_submit) {
          horizon.clearErrorMessages();
          horizon.alert('error', gettext('There was a problem communicating with the server, please try again.'));
        }
      }
    });
  },

  /*
   * Gets the html select element associated with a given
   * rule id for rule_id.
   **/
  get_rule_element: function(rule_id) {
    return $('label[for^="id_rule_' + rule_id + '"]');
  },

  /*
   * Initializes an associative array of lists of the current
   * rules.
   **/
  init_rule_list: function() {
    horizon.firewalls.rules_selected = [];
    horizon.firewalls.rules_available = [];
    $(this.get_rule_element("")).each(function(){
      var $this = $(this).parent();
      var $input = $this.children("input");
      var rule_property = {
        name:$this.text().replace(/^\s+/,""),
        id:$input.attr("id"),
        value:$input.attr("value")
      };
      if($input.is(':checked')) {
        horizon.firewalls.rules_selected.push(rule_property);
      } else {
        horizon.firewalls.rules_available.push(rule_property);
      }
    });
  },

  /*
   * Generates the HTML structure for a rule that will be displayed
   * as a list item in the rule list.
   **/
  generate_rule_element: function(name, value) {
    var $li = $('<li>');
    $li.attr('name', value).html(name + '<em class="rule_id">(' + value + ')</em><a href="#" class="btn btn-primary"></a>');
    return $li;
  },

  /*
   * Generates the HTML structure for the Rule List.
   **/
  generate_rulelist_html: function() {
    var self = this;
    var updateForm = function() {
      var lists = $("#ruleListId li").attr('data-index',100);
      var active_rules = $("#selected_rule > li").map(function(){
        return $(this).attr("name");
      });
      $("#ruleListId input:checkbox").removeAttr('checked');
      active_rules.each(function(index, value){
        $("#ruleListId input:checkbox[value=" + value + "]")
          .prop('checked', true)
          .parents("li").attr('data-index',index);
      });
      $("#ruleListId ul").html(
        lists.sort(function(a,b){
          if( $(a).data("index") < $(b).data("index")) { return -1; }
          if( $(a).data("index") > $(b).data("index")) { return 1; }
          return 0;
        })
      );
    };
    $("#ruleListSortContainer").show();
    $("#ruleListIdContainer").hide();
    self.init_rule_list();
    // Make sure we don't duplicate the rules in the list
    $("#available_rule").empty();
    $.each(self.rules_available, function(index, value){
      $("#available_rule").append(self.generate_rule_element(value.name, value.value));
    });
    // Make sure we don't duplicate the rules in the list
    $("#selected_rule").empty();
    $.each(self.rules_selected, function(index, value){
      $("#selected_rule").append(self.generate_rule_element(value.name, value.value));
    });
    $(".rulelist > li > a.btn").click(function(e){
      var $this = $(this);
      e.preventDefault();
      e.stopPropagation();
      if($this.parents("ul#available_rule").length > 0) {
        $this.parent().appendTo($("#selected_rule"));
      } else if ($this.parents("ul#selected_rule").length > 0) {
        $this.parent().appendTo($("#available_rule"));
      }
      updateForm();
    });
    if ($("#ruleListId > div.form-group.error").length > 0) {
      var errortext = $("#ruleListId > div.form-group.error").find("span.help-block").text();
      $("#selected_rule_h4").before($('<div class="dynamic-error">').html(errortext));
    }
    $(".rulelist").sortable({
      connectWith: "ul.rulelist",
      placeholder: "ui-state-highlight",
      distance: 5,
      start:function(){
        $("#selected_rule").addClass("dragging");
      },
      stop:function(){
        $("#selected_rule").removeClass("dragging");
        updateForm();
      }
    }).disableSelection();
  },

  /*
   * Gets the html select element associated with a given
   * router id for router_id.
   **/
  get_router_element: function(router_id) {
    return $('label[for^="id_router_' + router_id + '"]');
  },

  /*
   * Initializes an associative array of lists of the current
   * routers.
   **/
  init_router_list: function() {
    horizon.firewalls.routers_selected = [];
    horizon.firewalls.routers_available = [];
    $(this.get_router_element("")).each(function(){
      var $this = $(this).parent();
      var $input = $this.children("input");
      var router_property = {
        name:$this.text().replace(/^\s+/,""),
        id:$input.attr("id"),
        value:$input.attr("value")
      };
      if($input.is(':checked')) {
        horizon.firewalls.routers_selected.push(router_property);
      } else {
        horizon.firewalls.routers_available.push(router_property);
      }
    });
  },

  /*
   * Generates the HTML structure for a router that will be displayed
   * as a list item in the router list.
   **/
  generate_router_element: function(name, value) {
    var $li = $('<li>');
    $li.attr('name', value).html(name + '<em class="router_id">(' + value + ')</em><a href="#" class="btn btn-primary"></a>');
    return $li;
  },

  /*
   * Generates the HTML structure for the router List.
   **/
  generate_routerlist_html: function() {
    var self = this;
    var updateForm = function() {
      var lists = $("#routerListId li").attr('data-index',100);
      var active_routers = $("#selected_router > li").map(function(){
        return $(this).attr("name");
      });
      $("#routerListId input:checkbox").removeAttr('checked');
      active_routers.each(function(index, value){
        $("#routerListId input:checkbox[value=" + value + "]")
          .prop('checked', true)
          .parents("li").attr('data-index',index);
      });
      $("#routerListId ul").html(
        lists.sort(function(a,b){
          if( $(a).data("index") < $(b).data("index")) { return -1; }
          if( $(a).data("index") > $(b).data("index")) { return 1; }
          return 0;
        })
      );
    };
    $("#routerListSortContainer").show();
    $("#routerListIdContainer").hide();
    self.init_router_list();
    // Make sure we don't duplicate the routers in the list
    $("#available_router").empty();
    $.each(self.routers_available, function(index, value){
      $("#available_router").append(self.generate_router_element(value.name, value.value));
    });
    // Make sure we don't duplicate the routers in the list
    $("#selected_router").empty();
    $.each(self.routers_selected, function(index, value){
      $("#selected_router").append(self.generate_router_element(value.name, value.value));
    });
    $(".routerlist > li > a.btn").click(function(e){
      var $this = $(this);
      e.preventDefault();
      e.stopPropagation();
      if($this.parents("ul#available_router").length > 0) {
        $this.parent().appendTo($("#selected_router"));
      } else if ($this.parents("ul#selected_router").length > 0) {
        $this.parent().appendTo($("#available_router"));
      }
      updateForm();
    });
    if ($("#routerListId > div.form-group.error").length > 0) {
      var errortext = $("#routerListId > div.form-group.error").find("span.help-block").text();
      $("#selected_router_h4").before($('<div class="dynamic-error">').html(errortext));
    }
    $(".routerlist").sortable({
      connectWith: "ul.routerlist",
      placeholder: "ui-state-highlight",
      distance: 5,
      start:function(){
        $("#selected_router").addClass("dragging");
      },
      stop:function(){
        $("#selected_router").removeClass("dragging");
        updateForm();
      }
    }).disableSelection();
  },

  workflow_init: function() {
    // Initialise the drag and drop rule list
    horizon.firewalls.generate_rulelist_html();
    horizon.firewalls.generate_routerlist_html();
  }
};

horizon.addInitFunction(horizon.firewalls.init = function () {
  $(document).on('submit', '#tail_length', function (evt) {
    horizon.firewalls.user_decided_length = true;
    horizon.firewalls.getConsoleLog(true);
    evt.preventDefault();
  });
});
