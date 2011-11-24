(function($, window, document, undefined) {
  $.fn.columnar = function (target, opt) {
    var options = $.extend({
      trigger: 'change',
      retrieve: 'name',
      container: $('table'),
      selector: '.',
      selected_class: 'hidden'
    }, opt);

    $(this).bind(options.trigger, function(e) {
      options.container.find( options.selector + $(this).attr(options.retrieve) ).toggleClass(options.selected_class)
    })
  }
}(jQuery, this, document));


$(function(){
  $('.modal:not(.static_page) .cancel').live('click', function (evt) {
    $(this).closest('.modal').remove();
  });

  $('.ajax-modal').click(function (evt) {
    var $this = $(this);
    $.ajax($this.attr('href'), {
      complete: function (jqXHR, status) {
        $('body').append(jqXHR.responseText);
        $('body .modal:last').modal({'show':true, 'backdrop': true, 'keyboard': true});
      }
    });
    return false;
  });

  $('.table_search input').quicksearch('tr.odd, tr.even', {
    'delay': 300,
    'loader': 'span.loading',
    'bind': 'keyup click',
    'show': function () {
      this.style.color = '';
    },
    'hide': function () {
      this.style.color = '#ccc';
    },
    'prepareQuery': function (val) {
      return new RegExp(val, "i");
    },
    'testQuery': function (query, txt, _row) {
      return query.test($(_row).find('td:not(.hidden)').text());
    }
  });

  $('table#keypairs').tablesorter();

  $('#keypair_filter form input[type=checkbox]').columnar({});


  // show+hide image details
  $(".details").hide()
  $("#images td:not(#actions)").click(function(e){
    $(this).parent().nextUntil(".even, .odd").fadeToggle("slow");
  })

  $(".drop_btn").click(function(){
    $(this).parent().children('.item_list').toggle();
    return false;
  })


  // confirmation on deletion of items
  $(".terminate").click(function(e){
    var response = confirm('Are you sure you want to terminate the Instance: '+$(this).attr('title')+"?");
    return response;
  })

  $(".delete").click(function(e){
    var response = confirm('Are you sure you want to delete the '+$(this).attr('title')+" ?");
    return response;
  })

  $(".reboot").click(function(e){
    var response = confirm('Are you sure you want to reboot the '+$(this).attr('title')+" ?");
    return response;
  })

  $(".disable").click(function(e){
    var response = confirm('Are you sure you want to disable the '+$(this).attr('title')+" ?");
    return response;
  })

  $(".enable").click(function(e){
    var response = confirm('Are you sure you want to enable the '+$(this).attr('title')+" ?");
    return response;
  })

  // disable multiple submissions when launching a form
  $("form").submit(function() {
      $(this).submit(function() {
          return false;
      });
      return true;
  });

  // Fancy multi-selects
  $(".chzn-select").chosen()

  $(".detach").click(function(e){
    var response = confirm('Are you sure you want to detach the '+$(this).attr('title')+" ?");
    return response;
  })
})


