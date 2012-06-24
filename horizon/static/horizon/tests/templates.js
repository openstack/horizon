horizon.addInitFunction(function () {
    module("Client-Side Templating (horizon.templates.js)");

    test("Template Compilation", function () {
        ok(_.size(horizon.templates.compiled_templates) > 0, "Compiled templates list should not be empty.");
    });
});
