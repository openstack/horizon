# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


from horizon.test import helpers as test


class ServicesTests(test.JasmineTests):
    sources = [
        'horizon/js/horizon.js',
        'horizon/js/angular/horizon.conf.js',
        'horizon/js/angular/horizon.js',
        'horizon/js/angular/services/horizon.utils.js',
        'horizon/js/angular/hz.api.module.js',
        'horizon/js/angular/services/hz.api.service.js',
        'horizon/js/angular/services/hz.api.config.js',
        'angular/widget.module.js',
        'angular/action-list/action-list.js',
        'angular/action-list/button-tooltip.js',
        'angular/bind-scope/bind-scope.js',
        'angular/charts/charts.js',
        'angular/charts/chart-tooltip.js',
        'angular/charts/pie-chart.js',
        'angular/form/form.js',
        'angular/help-panel/help-panel.js',
        'angular/login/login.js',
        'angular/metadata-tree/metadata-tree.js',
        'angular/metadata-tree/metadata-tree-service.js',
        'angular/modal/modal.js',
        'angular/modal/modal-wait-spinner.js',
        'angular/table/table.js',
        'angular/table/basic-table.js',
        'angular/transfer-table/transfer-table.js',
        'angular/validators/validators.js',
        'angular/wizard/wizard.js',
        'angular/workflow/workflow.js',
        'angular/metadata-display/metadata-display.js',
        'horizon/js/angular/filters/filters.js',
    ]
    specs = [
        'horizon/js/angular/services/hz.api.service.spec.js',
        'horizon/js/angular/services/hz.api.config.spec.js',
        'horizon/tests/jasmine/utils.spec.js',
        'angular/action-list/action-list.spec.js',
        'angular/bind-scope/bind-scope.spec.js',
        'angular/charts/pie-chart.spec.js',
        'angular/form/form.spec.js',
        'angular/help-panel/help-panel.spec.js',
        'angular/login/login.spec.js',
        'angular/modal/modal.spec.js',
        'angular/modal/modal-wait-spinner.spec.js',
        'angular/table/table.spec.js',
        'angular/table/basic-table.spec.js',
        'angular/transfer-table/transfer-table.spec.js',
        'angular/wizard/wizard.spec.js',
        'angular/validators/validators.spec.js',
        'angular/workflow/workflow.spec.js',
        'angular/metadata-tree/metadata-tree.spec.js',
        'angular/metadata-display/metadata-display.spec.js',
        'horizon/js/angular/filters/filters.spec.js',
    ]
    externalTemplates = [
        'angular/action-list/action.html',
        'angular/action-list/menu-item.html',
        'angular/action-list/menu.html',
        'angular/action-list/single-button.html',
        'angular/action-list/split-button.html',
        'angular/charts/chart-tooltip.html',
        'angular/charts/pie-chart.html',
        'angular/help-panel/help-panel.html',
        'angular/table/search-bar.html',
        'angular/transfer-table/transfer-table.html',
        'angular/wizard/wizard.html',
        'angular/metadata-tree/metadata-tree.html',
        'angular/metadata-tree/metadata-tree-item.html',
        'angular/metadata-display/metadata-display.html',
    ]
