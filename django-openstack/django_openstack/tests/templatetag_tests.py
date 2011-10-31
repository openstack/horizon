import re

from django import dispatch, http, template
from django.utils.text import normalize_newlines

from django_openstack import signals, test


def single_line(text):
    ''' Quick utility to make comparing template output easier. '''
    return re.sub(' +',
                  ' ',
                  normalize_newlines(text).replace('\n', '')).strip()


class TemplateTagTests(test.TestCase):
    def setUp(self):
        super(TemplateTagTests, self).setUp()
        self._signal = self.mox.CreateMock(dispatch.Signal)

    def test_sidebar_modules(self):
        '''
        Tests for the sidebar module registration mechanism.

        The standard "ping" signal return value looks like this:

        tuple(<dash_apps_ping>, {
                'title': 'Nixon',
                'links': [{'url':'/syspanel/nixon/google',
                          'text':'Google', 'active_text': 'google'}],
                'type': 'syspanel',
            })
        '''
        self.mox.StubOutWithMock(signals, 'dash_modules_detect')
        signals_call = (
                (self._signal, {
                    'title': 'Nixon',
                    'links': [{'url':'/dash/nixon/google',
                            'text':'Google', 'active_text': 'google'}],
                    'type': 'dash',
                }),
                (self._signal, {
                    'title': 'Nixon',
                    'links': [{'url':'/syspanel/nixon/google',
                            'text':'Google', 'active_text': 'google'}],
                    'type': 'syspanel',
                }),
            )
        signals.dash_modules_detect().AndReturn(signals_call)
        signals.dash_modules_detect().AndReturn(signals_call)
        self.mox.ReplayAll()

        context = template.Context({'request': self.request})

        # Dash module is rendered correctly, and only in dash sidebar
        ttext = '{% load sidebar_modules %}{% dash_sidebar_modules request %}'
        t = template.Template(ttext)
        self.assertEqual(single_line(t.render(context)),
                         '<h3>Nixon</h3> <ul class="sub_nav"> <li>'
                         '<a href="/dash/nixon/google">Google</a></li> </ul>')

        # Syspanel module is rendered correctly and only in syspanel sidebar
        ttext = ('{% load sidebar_modules %}'
                 '{% syspanel_sidebar_modules request %}')
        t = template.Template(ttext)
        self.assertEqual(single_line(t.render(context)),
                         '<h3>Nixon</h3> <ul class="sub_nav"> <li>'
                         '<a href="/syspanel/nixon/google">Google</a></li>'
                         ' </ul>')

        self.mox.VerifyAll()
