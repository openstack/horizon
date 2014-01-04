horizon.firewalls = {
  user_decided_length: false,
  rules_selected: [],
  rules_available: [],

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
      error: function(response) {
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
    return $('li > label[for^="id_rule_' + rule_id + '"]');
  },

  /*
   * Initializes an associative array of lists of the current
   * rules.
   **/
  init_rule_list: function() {
    horizon.firewalls.rules_selected = [];
    horizon.firewalls.rules_available = [];
    $(this.get_rule_element("")).each(function(){
      var $this = $(this);
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
  generate_rule_element: function(name, id, value) {
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
      var lists = $("#ruleListId div.input li").attr('data-index',100);
      var active_rules = $("#selected_rule > li").map(function(){
        return $(this).attr("name");
      });
      $("#ruleListId div.input input:checkbox").removeAttr('checked');
      active_rules.each(function(index, value){
        $("#ruleListId div.input input:checkbox[value=" + value + "]")
          .attr('checked','checked')
          .parents("li").attr('data-index',index);
      });
      $("#ruleListId div.input ul").html(
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
      $("#available_rule").append(self.generate_rule_element(value.name, value.id, value.value));
    });
    // Make sure we don't duplicate the rules in the list
    $("#selected_rule").empty();
    $.each(self.rules_selected, function(index, value){
      $("#selected_rule").append(self.generate_rule_element(value.name, value.id, value.value));
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
    if ($("#ruleListId > div.control-group.error").length > 0) {
      var errortext = $("#ruleListId > div.control-group.error").find("span.help-inline").text();
      $("#selected_rule_h4").before($('<div class="dynamic-error">').html(errortext));
    }
    $(".rulelist").sortable({
      connectWith: "ul.rulelist",
      placeholder: "ui-state-highlight",
      distance: 5,
      start:function(e,info){
        $("#selected_rule").addClass("dragging");
      },
      stop:function(e,info){
        $("#selected_rule").removeClass("dragging");
        updateForm();
      }
    }).disableSelection();
  },

  workflow_init: function(modal) {
    // Initialise the drag and drop rule list
    horizon.firewalls.generate_rulelist_html();
  }
};

horizon.addInitFunction(function () {
  $(document).on('submit', '#tail_length', function (evt) {
    horizon.firewalls.user_decided_length = true;
    horizon.firewalls.getConsoleLog(true);
    evt.preventDefault();
  });
});
