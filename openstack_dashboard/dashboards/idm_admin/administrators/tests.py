from horizon.test import helpers as test


class AdministratorsTests(test.TestCase):
    # Unit tests for administrators.
    def test_me(self):
        self.assertTrue(1 + 1 == 2)
