$(function() {
  // Display notification message close boxes and wire up click handlers.
  $('.message .close').show().click(function() { $(this).closest('.message').fadeOut(); });
});