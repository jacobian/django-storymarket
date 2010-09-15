import os
import sys
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()
    
setup(
    name = "django-storymarket",
    version = "1.0a2",
    description = "Sync Django models to Storymarket.",
    long_description = read('README.rst'),
    url = 'http://packages.python.org/django-storymarket',
    license = 'BSD',
    author = 'Jacob Kaplan-Moss',
    author_email = 'jacob@jacobian.org',
    packages = find_packages(exclude=['tests', 'example']),
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    install_requires = ['django >= 1.2', 'python-storymarket'],
    tests_require = ["mock", "nose", "django-nose"],
    test_suite = "django_storymarket.runtests.runtests",
)