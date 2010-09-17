"""
Converters are the glue that converts a Django model into a dict of data to be
posted to Storymarket. This module implements a registry for them.

Converter functions are simple functions that take two arguments -- the
Storymarket API object and the model instance to convert -- and return
a dictionary of data to be used for the upload. This dict should be in
the simplified format accepted by the Storymarket API, and should have
one extra key: the type of data to be uploaded.

For example::

    def story_to_storymarket(api, obj):
        return {
            "type": "text",
            "title": obj.headline,
            "author": "jacobian",
            "org": api.orgs.get(MY_ORG_ID),
            "category": api.subcategories.get(SOME_CATEGORY_ID),
            "content": obj.body
        }

For binary types, the returned dict should have a ``blob`` key; the value can
either be the binary data as a string or (more likely) a file-like object::

    def image_to_storymarket(api, obj):
        return {
            "type": "photos",
            ...
            "blob": obj.image_field.open(),
        }
"""

print "conv"

import storymarket
from django.db import models
from django.conf import settings
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule

_registry = {}
_FALLBACK_KEY = '*'
_CONVERTER_MODULE_NAME = 'storymarket_converters'

def convert(instance):
    """
    Convert a model instance using its registered converter.
    
    If it fails, this'll raise :exc:`CannotConvert`.
    
    :param instance: The model instance to convert.
    :rtype: dict
    """
    autodiscover()
    api = storymarket.Storymarket(settings.STORYMARKET_API_KEY)
    
    # I'm using look-before-you-leap instead of better-to-ask-for-permission
    # here because a try/except might accidentally catch a KeyError raised
    # by the converter itself.
    registry_key = str(instance._meta)
    if registry_key in _registry:
        return _registry[registry_key](api, instance)
    elif _FALLBACK_KEY in _registry:
        return _registry[_FALLBACK_KEY](api, instance)
    else:
        raise CannotConvert("Can't convert %s objects." % instance._meta)

def registered_models():
    """
    Return a list of all models registered for conversion.
    """
    autodiscover()
    return filter(None, (models.get_model(*k.split('.')) for k in _registry.keys()))

class CannotConvert(Exception):
    pass

def register(model, callback):
    """
    Register a converter.
    
    :param model: The model class to register the converter for.
    :param callback: The conversion function.
    """
    _registry[str(model._meta)] = callback

def register_fallback_converter(callback):
    """
    Register a fallback converter to be used if a model-specific converter
    doesn't already exist.
    
    This converter should either convert an object or raise :exc:`CannotConvert`.
    
    :param callback: The conversion function.
    """
    _registry[_FALLBACK_KEY] = callback

def unregister(model):
    """
    Remove a converter for a model, if registered.
    
    :param model: The model class to unregister.
    """
    try:
        del _registry[str(model._meta)]
    except KeyError:
        pass

def unregister_fallback_converter():
    """
    Remove a fallback converter, if registered.
    """
    try:
        del _registry[_FALLBACK_KEY]
    except KeyError:
        pass

_discovery_done = False
def autodiscover():
    """
    Auto-discover converter modules from settings.INSTALLED_APPS.
    
    This code is cribbed from admin.autodiscover.
    """
    global _discovery_done
    if _discovery_done: return
    
    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        try:
            import_module("%s.%s" % (app, _CONVERTER_MODULE_NAME))
        except:
            # Ignore the error if the app just doesn't have a converter
            # module, but bubble it up if it was anything else.
            if module_has_submodule(mod, _CONVERTER_MODULE_NAME):
                raise
                
    _discovery_done = True