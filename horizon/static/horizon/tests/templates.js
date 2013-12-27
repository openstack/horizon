horizon.addInitFunction(function () {
  module("Client-Side Templating (horizon.templates.js)");

  test("Template Compilation", function () {
    var size = 0;
    angular.forEach(horizon.templates.compiled_templates, function () {
      size = size + 1;
    });
    ok(size > 0, "Compiled templates list should not be empty.");
  });
});
