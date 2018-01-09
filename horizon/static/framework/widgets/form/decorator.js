/**
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

(function() {
  'use strict';

  // Horizon custom decorator for angular schema form
  angular
    .module('schemaForm')
    .config(config);

  config.$inject = [
    'schemaFormDecoratorsProvider',
    'sfBuilderProvider',
    'sfPathProvider',
    'sfErrorMessageProvider',
    '$windowProvider',
    'hzBuilderProvider'
  ];

  function config(
    decoratorsProvider,
    sfBuilderProvider,
    sfPathProvider,
    sfErrorMessageProvider,
    $windowProvider,
    hzBuilderProvider
  ) {
    var base = $windowProvider.$get().STATIC_URL + 'framework/widgets/form/fields/';
    var simpleTransclusion = sfBuilderProvider.builders.simpleTransclusion;
    var ngModelOptions = sfBuilderProvider.builders.ngModelOptions;
    var ngModel = sfBuilderProvider.builders.ngModel;
    var sfField = sfBuilderProvider.builders.sfField;
    var condition = sfBuilderProvider.builders.condition;
    var array = sfBuilderProvider.builders.array;
    var tabs = hzBuilderProvider.$get().tabsBuilder;
    var defaults = [sfField, ngModel, ngModelOptions, condition];

    // Define all our templates
    decoratorsProvider.defineDecorator('bootstrapDecorator', {
      textarea: {
        template: base + 'textarea.html',
        builder: defaults
      },
      fieldset: {
        template: base + 'fieldset.html',
        builder: [sfField, simpleTransclusion, condition]
      },
      array: {
        template: base + 'array.html',
        builder: [sfField, ngModelOptions, ngModel, array, condition]
      },
      tabarray: {
        template: base + 'tabarray.html',
        builder: [sfField, ngModelOptions, ngModel, array, condition]
      },
      tabs: {
        template: base + 'tabs.html',
        builder: [sfField, ngModelOptions, tabs, condition]
      },
      section: {
        template: base + 'section.html',
        builder: [sfField, simpleTransclusion, condition]
      },
      conditional: {
        template: base + 'section.html',
        builder: [sfField, simpleTransclusion, condition]
      },
      select: {
        template: base + 'select.html',
        builder: defaults
      },
      checkbox: {
        template: base + 'checkbox.html',
        builder: defaults
      },
      checkboxes: {
        template: base + 'checkboxes.html',
        builder: [sfField, ngModelOptions, ngModel, array, condition]
      },
      number: {
        template: base + 'default.html',
        builder: defaults
      },
      password: {
        template: base + 'default.html',
        builder: defaults
      },
      submit: {
        template: base + 'submit.html',
        builder: defaults
      },
      button: {
        template: base + 'submit.html',
        builder: defaults
      },
      radios: {
        template: base + 'radios.html',
        builder: defaults
      },
      'radios-inline': {
        template: base + 'radios-inline.html',
        builder: defaults
      },
      radiobuttons: {
        template: base + 'radio-buttons.html',
        builder: defaults
      },
      'password-confirm': {
        template: base + 'password-confirm.html',
        builder: defaults
      },
      help: {
        template: base + 'help.html',
        builder: defaults
      },
      'default': {
        template: base + 'default.html',
        builder: defaults
      }
    }, []);

    // Define and register our validation messages
    // These are the error codes provided by the tv4 validator:
    // https://github.com/geraintluff/tv4/blob/master/source/api.js
    var defaultMessages = {
      "default": gettext("The data in this field is invalid"),
      0: gettext("Invalid type, expected {$schema.type$}"),
      1: gettext("No enum match for: {$viewValue$}"),
      10: gettext("Data does not match any schemas from 'anyOf'"),
      11: gettext("Data does not match any schemas from 'oneOf'"),
      12: gettext("Data is valid against more than one schema from 'oneOf'"),
      13: gettext("Data matches schema from 'not'"),
      // Numeric errors
      100: gettext("{$viewValue$} is not a multiple of {$schema.multipleOf$}"),
      101: gettext("{$viewValue$} is less than the allowed minimum of {$schema.minimum$}"),
      102: gettext("{$viewValue$} is equal to the exclusive minimum {$schema.minimum$}"),
      103: gettext("{$viewValue$} is greater than the allowed maximum of {$schema.maximum$}"),
      104: gettext("{$viewValue$} is equal to the exclusive maximum {$schema.maximum$}"),
      105: gettext("{$viewValue$} is not a valid number"),
      // String errors
      /* eslint-disable max-len */
      200: gettext("{$schema.title$} is too short ({$viewValue.length$} characters), minimum {$schema.minLength$}"),
      201: gettext("{$schema.title$} is too long ({$viewValue.length$} characters), maximum {$schema.maxLength$}"),
      /* eslint-enable max-len */
      202: gettext("{$schema.title$} is formatted incorrectly"),
      // Object errors
      300: gettext("Too few properties defined, minimum {$schema.minProperties$}"),
      301: gettext("Too many properties defined, maximum {$schema.maxProperties$}"),
      302: gettext("{$schema.title$} is a required field"),
      303: gettext("Additional properties not allowed"),
      304: gettext("Dependency failed - key must exist"),
      // Array errors
      400: gettext("Array is too short ({$value.length$} items), minimum {$schema.minItems$}"),
      401: gettext("Array is too long ({$value.length$} items), maximum {$schema.maxItems$}"),
      402: gettext("Array items must be unique"),
      403: gettext("Additional items not allowed"),
      // Format errors
      500: gettext("Format validation failed"),
      501: gettext("Keyword failed: '{$title$}'"),
      // Schema structure
      600: gettext("Circular $refs"),
      // Non-standard validation options
      1000: gettext("Unknown property (not in schema)")
    };

    sfErrorMessageProvider.setDefaultMessages(defaultMessages);
  }
})();
