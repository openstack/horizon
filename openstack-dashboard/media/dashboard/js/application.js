$(function(){
  $('input#table_search').quicksearch('tr.odd, tr.even');

  // show+hide image details
  $(".details").hide()
  $("td").click(function(e){
    $(this).parent().nextUntil(".even, .odd").fadeToggle("slow");
  })

  $("#user_tenant_list").hide()
  $("#drop_btn").click(function(){
    $("#user_tenant_list").toggle();
  })


  // confirmation on deletion of items
  $(".delete_link").click(function(e){
    var response = confirm('Are you sure you want to delete the '+$(this).attr('title')+" ?");
    return response;
  })

  $(".reboot_link").click(function(e){
    var response = confirm('Are you sure you want to reboot the '+$(this).attr('title')+" ?");
    return response;
  })


  // disable multiple submissions when launching a form
  $("form").submit(function() {
      $(this).submit(function() {
          return false;
      });
      return true;
  });
  
})