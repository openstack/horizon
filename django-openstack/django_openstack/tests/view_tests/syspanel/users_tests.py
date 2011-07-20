from django.core.urlresolvers import reverse
from django_openstack import api
from django_openstack.tests.view_tests import base
from mox import IgnoreArg
from openstackx.api import exceptions as api_exceptions

class UsersViewTests(base.BaseViewTests):
    def setUp(self):
        super(UsersViewTests, self).setUp()

        self.user = self.mox.CreateMock(api.User)
        self.user.enabled = True
        self.user.id = self.TEST_USER
        self.user.tenantId = self.TEST_TENANT

        self.users = [self.user]

    def test_index(self):
        self.mox.StubOutWithMock(api, 'user_list')
        api.user_list(IgnoreArg()).AndReturn(self.users)

        self.mox.ReplayAll()

        res = self.client.get(reverse('syspanel_users'))

        self.assertTemplateUsed(res, 'syspanel_users.html')
        self.assertItemsEqual(res.context['users'], self.users)

        self.mox.VerifyAll()

    def test_enable_user(self):
        OTHER_USER = 'otherUser'
        formData = {'method': 'UserEnableDisableForm',
                    'id': OTHER_USER,
                    'enabled': 'enable'}

        self.mox.StubOutWithMock(api, 'user_update_enabled')
        api.user_update_enabled(IgnoreArg(), OTHER_USER, True).AndReturn(
                self.mox.CreateMock(api.User))

        self.mox.ReplayAll()

        res = self.client.post(reverse('syspanel_users'), formData)

        self.assertRedirectsNoFollow(res, reverse('syspanel_users'))

        self.mox.VerifyAll()

    def test_disable_user(self):
        OTHER_USER = 'otherUser'
        formData = {'method': 'UserEnableDisableForm',
                    'id': OTHER_USER,
                    'enabled': 'disable'}

        self.mox.StubOutWithMock(api, 'user_update_enabled')
        api.user_update_enabled(IgnoreArg(), OTHER_USER, False).AndReturn(
                self.mox.CreateMock(api.User))

        self.mox.ReplayAll()

        res = self.client.post(reverse('syspanel_users'), formData)

        self.assertRedirectsNoFollow(res, reverse('syspanel_users'))

        self.mox.VerifyAll()

    def test_enable_disable_user_exception(self):
        OTHER_USER = 'otherUser'
        formData = {'method': 'UserEnableDisableForm',
                    'id': OTHER_USER,
                    'enabled': 'enable'}

        self.mox.StubOutWithMock(api, 'user_update_enabled')
        api_exception = api_exceptions.ApiException('apiException', message='apiException')
        api.user_update_enabled(IgnoreArg(), OTHER_USER, True).AndRaise(api_exception)

        self.mox.ReplayAll()

        res = self.client.post(reverse('syspanel_users'), formData)

        self.assertRedirectsNoFollow(res, reverse('syspanel_users'))

        self.mox.VerifyAll()
