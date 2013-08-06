horizon.addInitFunction(function () {
    module('Coding Style (jsHint)');

    test('jsHint', function () {
        expect(0);

        config = {
            // Warnings reported by JSHint. Suppressing for now...
            'asi': true,   // missing semicolons
            '-W004': true, // already defined
            '-W009': true, // array literal notation [] is preferrable
            '-W014': true, // bad line breaking
            '-W018': true, // confusing use
            '-W038': true, // out of scope
            '-W041': true, // use '!==' or  '===' for comparison
            '-W046': true, // extra leading zeros
            '-W069': true, // better written in dot notation
            '-W065': true, // missing radix parameter
            '-W075': true, // duplicate key
            '-W080': true, // it's not necessary to initialize to 'undefined'
            '-W093': true, // conditional instead of an assignment

            // Proposed set of rules
            //'camelcase' : true,
            //'indent': 2,
            //'undef': true,
            //'quotmark': 'single',
            //'maxlen': 80,
            //'trailing': true,
            //'curly': true
        };

        jsHintTest('horizon.communication.js', '/static/horizon/js/horizon.communication.js', config);
        jsHintTest('horizon.conf.js', '/static/horizon/js/horizon.conf.js', config);
        jsHintTest('horizon.cookies.js', '/static/horizon/js/horizon.cookies.js', config);
        jsHintTest('horizon.d3linechart.js', '/static/horizon/js/horizon.d3linechart.js', config);
        jsHintTest('horizon.d3piechart.js', '/static/horizon/js/horizon.d3piechart.js', config);
        jsHintTest('horizon.firewalls.js', '/static/horizon/js/horizon.firewalls.js', config);
        jsHintTest('horizon.forms.js', '/static/horizon/js/horizon.forms.js', config);
        jsHintTest('horizon.heattop.js', '/static/horizon/js/horizon.heattop.js', config);
        jsHintTest('horizon.instances.js', '/static/horizon/js/horizon.instances.js', config);
        jsHintTest('horizon.js', '/static/horizon/js/horizon.js', config);
        jsHintTest('horizon.membership.js', '/static/horizon/js/horizon.membership.js', config);
        jsHintTest('horizon.messages.js', '/static/horizon/js/horizon.messages.js', config);
        jsHintTest('horizon.modals.js', '/static/horizon/js/horizon.modals.js', config);
        jsHintTest('horizon.networktopology.js', '/static/horizon/js/horizon.networktopology.js', config);
        jsHintTest('horizon.quota.js', '/static/horizon/js/horizon.quota.js', config);
        jsHintTest('horizon.tables.js', '/static/horizon/js/horizon.tables.js', config);
        jsHintTest('horizon.tabs.js', '/static/horizon/js/horizon.tabs.js', config);
        jsHintTest('horizon.templates.js', '/static/horizon/js/horizon.templates.js', config);
        jsHintTest('horizon.users.js', '/static/horizon/js/horizon.users.js', config);
        jsHintTest('horizon.utils.js', '/static/horizon/js/horizon.utils.js', config);

        jsHintTest('tests/jshint.js', '/static/horizon/tests/jshint.js', config);
        jsHintTest('tests/messages.js', '/static/horizon/tests/messages.js', config);
        jsHintTest('tests/modals.js', '/static/horizon/tests/modals.js', config);
        jsHintTest('tests/tables.js', '/static/horizon/tests/tables.js', config);
        jsHintTest('tests/templates.js', '/static/horizon/tests/templates.js', config);
    });
});

