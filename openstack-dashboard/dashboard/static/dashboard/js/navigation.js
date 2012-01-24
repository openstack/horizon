horizon.addInitFunction(function() {
  // Show/hide tenant list in left nav.
  $(".drop_btn").click(function(){
    $(this).parent().children('.item_list').toggle();
    return false;
  });

  // Show/hide image details.
  $(".details").hide();
  $("#images td:not(#actions)").click(function(e) {
    $(this).parent().nextUntil(".even, .odd").fadeToggle("slow");
  });
});
