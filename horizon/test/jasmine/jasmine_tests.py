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
        'horizon/js/angular/controllers/metadata-widget-controller.js',
        'horizon/js/angular/hz.api.module.js',
        'horizon/js/angular/services/hz.api.service.js',
        'angular/widget.module.js',
        'angular/help-panel/help-panel.js',
        'angular/wizard/wizard.js',
        'angular/table/table.js',
        'angular/modal/modal.js',
        'angular/bind-scope/bind-scope.js',
        'angular/transfer-table/transfer-table.js',
    ]
    specs = [
        'horizon/tests/jasmine/utilsSpec.js',
        'horizon/tests/jasmine/metadataWidgetControllerSpec.js',
        'horizon/js/angular/services/hz.api.service.spec.js',
        'angular/help-panel/help-panel.spec.js',
        'angular/wizard/wizard.spec.js',
        'angular/table/table.spec.js',
        'angular/modal/simple-modal.spec.js',
        'angular/bind-scope/bind-scope.spec.js',
        'angular/transfer-table/transfer-table.spec.js',
    ]
    externalTemplates = [
        'angular/help-panel/help-panel.html',
        'angular/wizard/wizard.html',
        'angular/transfer-table/transfer-table.html',
    ]
