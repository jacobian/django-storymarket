Django bindings to the Storymarket API
======================================

.. module:: django_storymarket
   :synopsis: Sync Django models to Storymarket
   
.. currentmodule:: django_storymarket

This library binds Django models to the `Storymarket API
<http://storymarket.com/api/v1/>`_.

You'll need a Storymarket account to use this library, and you'll need to
generate an API token by visiting the 
`Developer API page <http://storymarket.com/users/api/>`_.

.. warning::

    This library is, at best, of beta quality. It works, but is
    under-tested and -documented, prone to API changes, and likely has
    bugs. At this point in time it should be considered a sketch, not
    a finished work.

Getting started
---------------

First, add your Storymarket API key to your settings module::

    STORYMARKET_API_KEY = '80ae06462d691445834ed2263677b795'
    
And make sure ``"django_storymarket"`` is in your ``INSTALLED_APPS`` and
you've run ``syncdb``.
    
Next, each model that you want to sync needs to have a converting function
defined and registered. Here's an example::
    
    import django_storymarket.converters
    from yourapp.models import ExampleStory

    def story_to_storymarket(api, obj):
       return {
           "type": "text",
           "title": obj.headline,
           "author": "jacobian",
           "org": api.orgs.get(12),
           "category": api.subcategories.get(12),
           "content": obj.body,
       }

    django_storymarket.converters.register(ExampleStory, story_to_storymarket)   
    
Of note here:
    
    * The conversion function takes an instance of the
      :class:`~storymarket.Storymarket` API object and the Django model to
      convert.

    * It must return a dictionary of converted data. This dictionary should
      be in the form described `in the python-storymarket documentation`__
      with one additional key: the ``type`` of object to upload. This type
      must be one of ``"audio"``, ``"data"``, ``"photos"``, ``"text"``, or
      ``"video"``.
      
    * This dictionary *may* be overridden by users, but it also might not
      be, so it must contain a full, valid set of data.
      
    * Binary object types must return an additional ``blob`` field. Its
      value should be a string of binary data or a file-like object.
      
__ http://packages.python.org/python-storymarket/content.html#uploading-new-objects

You may define these functions and register them anywhere. However, if you
place a ``storymarket_converters.py`` in any app directory it'll be loaded
automatically and can be used as a convenient place to register converters.

Finally, you need to hook the upload functions into the admin interface.
``django-storymarket`` ships with admin actions and a quasi-inline type.
Together, these allow bulk uploads from changelist pages and individual
uploads from object detail pages. Wire 'em into the admin like so::

    from django.contrib import admin
    from django_storymarket.admin import (upload_to_storymarket,
                                          is_synced_to_storymarket,
                                          StorymarketUploaderInline)
    from yourapp.models import ExampleStory

    class ExampleStoryAdmin(admin.ModelAdmin):
        actions = [upload_to_storymarket]
        list_display = ['headline', is_synced_to_storymarket]
        inlines = [StorymarketUploaderInline]

    admin.site.register(ExampleStory, ExampleStoryAdmin)
    
Of course, each of these bits is optional; you can mix and match.

More detailed documentation doesn't yet exist, sadly.

Contributing
------------

Run tests with ``python setup.py test``.

Development takes place 
`on GitHub <http://github.com/jacobian/django-storymarket>`_; please file
bugs/pull requests there.

Development on this project was funded by the 
`Lawrence Journal-World <http://ljworld.com/>`_ - thanks!

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

