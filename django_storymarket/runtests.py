"""
Test support harness for doing setup.py test.
See http://ericholscher.com/blog/2009/jun/29/enable-setuppy-test-your-django-apps/.
"""
import sys

# Bootstrap Django's settings.
from django.conf import settings
settings.configure(
    DATABASES = {
        'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory;'}
    },
    INSTALLED_APPS = ['django_storymarket'],
)

def runtests():
    """Test runner for setup.py test."""
    # Run you some tests.
    import django.test.utils
    runner_class = django.test.utils.get_runner(settings)
    test_runner = runner_class(verbosity=0, interactive=True)
    failures = test_runner.run_tests(['django_storymarket'])
    sys.exit(failures)
