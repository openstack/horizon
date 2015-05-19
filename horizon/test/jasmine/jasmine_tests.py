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
        'framework/widget.module.js',
        'framework/action-list/action-list.js',
        'framework/action-list/button-tooltip.js',
        'framework/bind-scope/bind-scope.js',
        'framework/charts/charts.js',
        'framework/charts/chart-tooltip.js',
        'framework/charts/pie-chart.js',
        'framework/form/form.js',
        'framework/help-panel/help-panel.js',
        'framework/login/login.js',
        'framework/metadata-tree/metadata-tree.js',
        'framework/metadata-tree/metadata-tree-service.js',
        'framework/modal/modal.js',
        'framework/modal/modal-wait-spinner.js',
        'framework/table/table.js',
        'framework/table/basic-table.js',
        'framework/transfer-table/transfer-table.js',
        'framework/validators/validators.js',
        'framework/wizard/wizard.js',
        'framework/workflow/workflow.js',
        'framework/metadata-display/metadata-display.js',
        'framework/toast/toast.js',
        'framework/i18n/i18n.js',
        'horizon/js/angular/filters/filters.js',
    ]
    specs = [
        'horizon/js/angular/services/hz.api.service.spec.js',
        'horizon/js/angular/services/hz.api.config.spec.js',
        'horizon/tests/jasmine/utils.spec.js',
        'framework/action-list/action-list.spec.js',
        'framework/bind-scope/bind-scope.spec.js',
        'framework/charts/pie-chart.spec.js',
        'framework/form/form.spec.js',
        'framework/help-panel/help-panel.spec.js',
        'framework/login/login.spec.js',
        'framework/modal/modal.spec.js',
        'framework/modal/modal-wait-spinner.spec.js',
        'framework/table/table.spec.js',
        'framework/table/basic-table.spec.js',
        'framework/transfer-table/transfer-table.spec.js',
        'framework/wizard/wizard.spec.js',
        'framework/validators/validators.spec.js',
        'framework/workflow/workflow.spec.js',
        'framework/metadata-tree/metadata-tree.spec.js',
        'framework/metadata-display/metadata-display.spec.js',
        'framework/toast/toast.spec.js',
        'framework/i18n/i18n.spec.js',
        'horizon/js/angular/filters/filters.spec.js',
    ]
    externalTemplates = [
        'framework/action-list/action.html',
        'framework/action-list/menu-item.html',
        'framework/action-list/menu.html',
        'framework/action-list/single-button.html',
        'framework/action-list/split-button.html',
        'framework/charts/chart-tooltip.html',
        'framework/charts/pie-chart.html',
        'framework/help-panel/help-panel.html',
        'framework/table/search-bar.html',
        'framework/transfer-table/transfer-table.html',
        'framework/wizard/wizard.html',
        'framework/metadata-tree/metadata-tree.html',
        'framework/metadata-tree/metadata-tree-item.html',
        'framework/metadata-display/metadata-display.html',
        'framework/toast/toast.html',
    ]
