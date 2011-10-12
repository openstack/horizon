from django_openstack import context_processors, test


class ContextProcessorTests(test.TestCase):
    def setUp(self):
        super(ContextProcessorTests, self).setUp()
        self._prev_catalog = self.request.user.service_catalog

    def tearDown(self):
        super(ContextProcessorTests, self).tearDown()
        self.request.user.service_catalog = self._prev_catalog

    def test_object_store(self):
        # Returns the object store service data when it's in the catalog
        object_store = context_processors.object_store(self.request)
        self.assertNotEqual(None, object_store['object_store_configured'])

        # Returns None when the object store is not in the catalog
        new_catalog = [service for service in self.request.user.service_catalog
                            if service['type'] != 'object-store']
        self.request.user.service_catalog = new_catalog
        object_store = context_processors.object_store(self.request)
        self.assertEqual(None, object_store['object_store_configured'])
