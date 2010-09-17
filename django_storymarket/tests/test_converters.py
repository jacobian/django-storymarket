import mock
from nose.tools import assert_equal
from django.conf import settings
from django_storymarket import converters
from django_storymarket.models import SyncedObject

def test_autodiscover():
    converters._discovery_done = False
    with mock.patch.object(converters, 'import_module') as mocked:

        # Under test, INSTALLED_APPS == ['django_storymarket'], so we'd
        # expect django_storymarket.storymarket_converters to be imported by
        # autodisocver()
        converters.autodiscover()
        mocked.assert_called_with('django_storymarket.storymarket_converters')
        assert converters._discovery_done
        
        # A second autodiscover will *not* reimport the module.
        mocked.reset_mock()
        converters.autodiscover()
        assert not mocked.called
        
def test_register():
    converters._registry = {}
    callback = lambda: {}
    
    converters.register(SyncedObject, callback)
    assert_equal(converters.registered_models(), [SyncedObject])
    
    converters.unregister(SyncedObject)
    assert_equal(converters.registered_models(), [])