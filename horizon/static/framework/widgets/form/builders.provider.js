/**
 * (c) Copyright 2016 Cisco Systems
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use self file except in compliance with the License. You may obtain
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

  angular
    .module('schemaForm')
    .provider('hzBuilder', provider);

  /**
   * @ngDoc provider
   * @name horizon.framework.widgets.form.builders
   */
  function provider() {
    var builders = {
      tabsBuilder: tabsBuilder
    };

    this.$get = function() {
      return builders;
    };

    function tabsBuilder(args) {
      if (args.form.tabs && args.form.tabs.length > 0) {
        var tabLi = args.fieldFrag.querySelector('li');
        /* eslint-disable max-len */
        tabLi.setAttribute('ng-if', '!tab.condition ? true : evalExpr(tab.condition, { model: model, "arrayIndex": $index })');
        /* eslint-enable max-len */
        var tabContent = args.fieldFrag.querySelector('.tab-content');

        args.form.tabs.forEach(function(tab, index) {
          tab.items.forEach(function(item) {
            if (item.required) {
              tab.required = true;
            }
          });
          var div = document.createElement('div');
          div.setAttribute('ng-show', 'model.tabs.selected === ' + index);
          div.setAttribute('ng-if', tab.condition || true);

          var childFrag = args.build(
            tab.items,
            args.path + '.tabs[' + index + '].items',
            args.state
          );
          div.appendChild(childFrag);
          tabContent.appendChild(div);
        });
      }
    }
  }
})();
