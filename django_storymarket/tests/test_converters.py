import mock
from nose.tools import assert_equal
from django.conf import settings
from django_storymarket import converters
from django_storymarket.models import SyncedObject

def test_autodiscover():
    converters._discovery_done = False
    with mock.patch.object(converters, 'import_module') as mocked:

        # We expect import_module to be called once for each module in INSTALLED_APPS
        converters.autodiscover()
        imported_modules = [call_args[0] for (call_args, call_kwargs) in mocked.call_args_list]
        for app in settings.INSTALLED_APPS:
            expected = '%s.%s' % (app, 'storymarket_converters')
            assert expected in imported_modules, "%r not found in %r" % (expected, imported_modules)
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