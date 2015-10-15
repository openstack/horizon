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

from django.core.urlresolvers import reverse
from django import http

from mox3.mox import IsA  # noqa
import six

from oslo_serialization import jsonutils

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from openstack_dashboard.test.test_data import utils as test_utils


INDEX_URL = reverse('horizon:admin:metering:index')
CREATE_URL = reverse('horizon:admin:metering:create')
SAMPLES_URL = reverse('horizon:admin:metering:samples')


class MeteringViewTests(test.BaseAdminViewTests):
    def test_create_report_page(self):
        formData = {'period': 7}
        res = self.client.get(CREATE_URL)
        self.assertTemplateUsed(res, 'admin/metering/daily.html')
        res = self.client.post(CREATE_URL, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_create_report_dates_messed_up(self):
        # dates are swapped in create report form
        formData = {'period': 'other',
                    'date_to': '2014-01-01',
                    'date_from': '2014-02-02'}

        res = self.client.post(CREATE_URL, formData)
        self.assertFormError(res, "form", "date_to",
                             ['Start must be earlier than end of period.'])

    def test_create_report_date_missing(self):
        formData = {'period': 'other',
                    'date_to': '2014-01-01',
                    'date_from': ''}

        res = self.client.post(CREATE_URL, formData)
        self.assertFormError(res, "form", "date_from",
                             ['Must specify start of period'])


class MeteringLineChartTabTests(test.BaseAdminViewTests):
    def setUp(self):
        test.BaseAdminViewTests.setUp(self)
        self.testdata = test_utils.TestData()
        test_utils.load_test_data(self.testdata)

    def _verify_series(self, series, value, date, expected_names):
        data = jsonutils.loads(series)
        self.assertTrue('series' in data)
        self.assertEqual(len(data['series']), len(expected_names))
        for d in data['series']:
            self.assertTrue('data' in d)
            self.assertEqual(len(d['data']), 1)
            self.assertAlmostEqual(d['data'][0].get('y'), value)
            self.assertEqual(d['data'][0].get('x'), date)
            self.assertEqual(d.get('unit'), '')
            self.assertIn(d.get('name'), expected_names)
            expected_names.remove(d.get('name'))

        self.assertEqual(data.get('settings'), {})

    @test.create_stubs({api.keystone: ('tenant_list',),
                        api.ceilometer: ('sample_list',
                                         'statistic_list',
                                         ), })
    def test_stats_for_line_chart(self):
        api.ceilometer.sample_list(IsA(http.HttpRequest),
                                   IsA(six.text_type),
                                   limit=IsA(int)).AndReturn([])
        api.ceilometer.statistic_list(IsA(http.HttpRequest),
                                      'memory',
                                      period=IsA(int),
                                      query=IsA(list)).MultipleTimes()\
            .AndReturn(self.testdata.statistics.list())
        api.keystone.tenant_list(IsA(http.HttpRequest),
                                 domain=None,
                                 paginate=False) \
            .AndReturn([self.testdata.tenants.list(), False])

        self.mox.ReplayAll()

        # get all statistics of project aggregates
        res = self.client.get(
            reverse('horizon:admin:metering:samples') +
            "?meter=memory&group_by=project&stats_attr=avg&date_options=7")

        self.assertEqual(res._headers['content-type'],
                         ('Content-Type', 'application/json'))
        expected_names = ['test_tenant',
                          'disabled_tenant',
                          u'\u4e91\u89c4\u5219']
        self._verify_series(res._container[0], 4.55, '2012-12-21T11:00:55',
                            expected_names)

    @test.create_stubs({api.keystone: ('tenant_list',),
                        api.ceilometer: ('sample_list',
                                         'statistic_list',
                                         ), })
    def test_stats_for_line_chart_attr_max(self):
        api.ceilometer.sample_list(IsA(http.HttpRequest),
                                   IsA(six.text_type),
                                   limit=IsA(int)).AndReturn([])
        api.ceilometer.statistic_list(IsA(http.HttpRequest),
                                      'memory', period=IsA(int),
                                      query=IsA(list))\
            .MultipleTimes().AndReturn(self.testdata.statistics.list())
        api.keystone.tenant_list(IsA(http.HttpRequest),
                                 domain=None,
                                 paginate=False) \
            .AndReturn([self.testdata.tenants.list(), False])

        self.mox.ReplayAll()

        # get all statistics of project aggregates
        res = self.client.get(
            reverse('horizon:admin:metering:samples') +
            "?meter=memory&group_by=project&stats_attr=max&date_options=7")

        self.assertEqual(res._headers['content-type'],
                         ('Content-Type', 'application/json'))
        expected_names = ['test_tenant',
                          'disabled_tenant',
                          u'\u4e91\u89c4\u5219']

        self._verify_series(res._container[0], 9.0, '2012-12-21T11:00:55',
                            expected_names)

    @test.create_stubs({api.keystone: ('tenant_list',),
                        api.ceilometer: ('sample_list',
                                         'resource_list',
                                         'statistic_list'
                                         ), })
    def test_stats_for_line_chart_no_group(self):
        api.ceilometer.sample_list(IsA(http.HttpRequest),
                                   IsA(six.text_type),
                                   limit=IsA(int)).AndReturn([])
        api.ceilometer.resource_list(IsA(http.HttpRequest), query=None,
                                     ceilometer_usage_object=None)\
            .AndReturn(self.testdata.api_resources.list())
        api.ceilometer.statistic_list(IsA(http.HttpRequest),
                                      'memory', period=IsA(int),
                                      query=IsA(list))\
            .MultipleTimes().AndReturn(self.testdata.statistics.list())
        api.keystone.tenant_list(IsA(http.HttpRequest),
                                 domain=None,
                                 paginate=False) \
            .AndReturn([self.testdata.tenants.list(), False])

        self.mox.ReplayAll()

        # get all statistics of the meter
        res = self.client.get(
            reverse('horizon:admin:metering:samples') +
            "?meter=memory&stats_attr=max&date_options=7")

        self.assertEqual(res._headers['content-type'],
                         ('Content-Type', 'application/json'))

        expected_names = ['fake_resource_id3']

        self._verify_series(res._container[0], 9.0, '2012-12-21T11:00:55',
                            expected_names)
