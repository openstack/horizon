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
        'openstack-service-api/openstack-service-api.module.js',
        'openstack-service-api/settings.service.js',
        'openstack-service-api/cinder.service.js',
        'openstack-service-api/glance.service.js',
        'openstack-service-api/keystone.service.js',
        'openstack-service-api/neutron.service.js',
        'openstack-service-api/nova.service.js',
        'openstack-service-api/policy.service.js',
        'openstack-service-api/security-group.service.js',

        'auth/auth.module.js',
        'auth/login/login.module.js',
        'auth/login/login.controller.js',
        'auth/login/login-finder.directive.js',

        'dashboard-app/dashboard-app.module.js',

        'framework/framework.module.js',

        'framework/conf/conf.js',

        'framework/util/util.module.js',
        'framework/util/bind-scope/bind-scope.js',
        'framework/util/filters/filters.js',
        'framework/util/http/http.js',
        'framework/util/i18n/i18n.js',
        'framework/util/validators/validators.js',
        'framework/util/workflow/workflow.js',
        'framework/util/tech-debt/tech-debt.module.js',
        'framework/util/tech-debt/helper-functions.js',
        'framework/util/tech-debt/image-file-on-change.js',

        'framework/widgets/widgets.module.js',
        'framework/widgets/action-list/action-list.js',
        'framework/widgets/action-list/button-tooltip.js',
        'framework/widgets/charts/charts.module.js',
        'framework/widgets/charts/chart-tooltip.directive.js',
        'framework/widgets/charts/pie-chart.directive.js',
        'framework/widgets/help-panel/help-panel.js',
        'framework/widgets/magic-search/magic-search.js',
        'framework/widgets/metadata-tree/metadata-tree.module.js',
        'framework/widgets/metadata-tree/metadata-tree-service.js',
        'framework/widgets/modal/modal.module.js',
        'framework/widgets/modal/modal.controller.js',
        'framework/widgets/modal/modal.factory.js',
        'framework/widgets/modal-wait-spinner/modal-wait-spinner.js',
        'framework/widgets/table/table.module.js',
        'framework/widgets/table/basic-table.js',
        'framework/widgets/transfer-table/transfer-table.js',
        'framework/widgets/wizard/wizard.js',
        'framework/widgets/metadata-display/metadata-display.js',
        'framework/widgets/toast/toast.module.js',
        'framework/widgets/toast/toast.directive.js',
        'framework/widgets/toast/toast.factory.js',
    ]
    specs = [
        'auth/login/login.spec.js',

        'openstack-service-api/common-test.spec.js',
        'openstack-service-api/settings.service.spec.js',
        'openstack-service-api/cinder.service.spec.js',
        'openstack-service-api/glance.service.spec.js',
        'openstack-service-api/keystone.service.spec.js',
        'openstack-service-api/neutron.service.spec.js',
        'openstack-service-api/nova.service.spec.js',
        'openstack-service-api/policy.service.spec.js',
        'openstack-service-api/security-group.service.spec.js',

        'framework/util/bind-scope/bind-scope.spec.js',
        'framework/util/filters/filters.spec.js',
        'framework/util/http/http.spec.js',
        'framework/util/i18n/i18n.spec.js',
        'framework/util/tech-debt/helper-functions.spec.js',
        'framework/util/validators/validators.spec.js',
        'framework/util/workflow/workflow.spec.js',

        'framework/widgets/action-list/action-list.spec.js',
        'framework/widgets/charts/charts.spec.js',
        'framework/widgets/charts/chart-tooltip.spec.js',
        'framework/widgets/charts/pie-chart.spec.js',
        'framework/widgets/help-panel/help-panel.spec.js',
        'framework/widgets/magic-search/magic-search.spec.js',
        'framework/widgets/modal/modal.spec.js',
        'framework/widgets/modal-wait-spinner/modal-wait-spinner.spec.js',
        'framework/widgets/table/table.spec.js',
        'framework/widgets/table/basic-table.spec.js',
        'framework/widgets/transfer-table/transfer-table.spec.js',
        'framework/widgets/wizard/wizard.spec.js',
        'framework/widgets/metadata-tree/metadata-tree.spec.js',
        'framework/widgets/metadata-display/metadata-display.spec.js',
        'framework/widgets/toast/toast.spec.js',
    ]
    externalTemplates = [
        'framework/widgets/action-list/action.html',
        'framework/widgets/action-list/menu-item.html',
        'framework/widgets/action-list/menu.html',
        'framework/widgets/action-list/single-button.html',
        'framework/widgets/action-list/split-button.html',
        'framework/widgets/charts/chart-tooltip.html',
        'framework/widgets/charts/pie-chart.html',
        'framework/widgets/help-panel/help-panel.html',
        'framework/widgets/magic-search/magic-search.html',
        'framework/widgets/table/search-bar.html',
        'framework/widgets/transfer-table/transfer-table.html',
        'framework/widgets/wizard/wizard.html',
        'framework/widgets/metadata-tree/metadata-tree.html',
        'framework/widgets/metadata-tree/metadata-tree-item.html',
        'framework/widgets/metadata-display/metadata-display.html',
        'framework/widgets/toast/toast.html',
    ]
