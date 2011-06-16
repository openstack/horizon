$(function(){
  $("#login").hide()
  $("#login_btn").click(function(){
    $("#login").toggle("fast")
  })
  
  $('input#table_search').quicksearch('tr.odd, tr.even');
  
  
  // show+hide image details
  $(".details").hide()
  $("td").click(function(e){
    $(this).parent().nextUntil(".even, .odd").fadeToggle("slow")
  })
  
  $("#user_tenant_list").hide()
  $("#drop_btn").click(function(){
    $("#user_tenant_list").toggle()
  })
})