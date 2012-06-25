/* Utilities for common needs which aren't JS builtins. */
horizon.utils = {
  capitalize: function(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
  },
  // Truncate a string at the desired length
  truncate: function(string, size, includeEllipsis) {
    var ellip = "";
    if(includeEllipsis) {
      ellip = "&hellip;";
    }
    if(string.length > size) {
      return string.substring(0, size) + ellip;
    } else {
      return string;
    }
  }
};
