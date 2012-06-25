/* Convenience functions for dealing with namespaced Horizon cookies. */
horizon.cookies = {
  read: function (cookie_name) {
    // Read in a cookie which contains JSON, and return a parsed object.
    var cookie = $.cookie("horizon." + cookie_name);
    if (cookie === null) {
      return {};
    }
    return $.parseJSON(cookie);
  },
  write: function (cookie_name, data) {
    // Overwrites a cookie.
    $.cookie("horizon." + cookie_name, JSON.stringify(data), {path: "/"});
  },
  update: function (cookie_name, key, value) {
    var data = horizon.cookies.read("horizon." + cookie_name);
    data[key] = value;
    horizon.cookies.write(cookie_name, data);
  },
  remove: function (cookie_name) {
    $.cookie("horizon." + cookie_name, null);
  }
};
