import mock
import unittest
from django.conf import settings
from django_storymarket import utils
from django_storymarket.models import SyncedObject

def test_save_to_storymarket():
    utils.QUEUE_UPLOADS = False
    settings.STORYMARKET_API_KEY = '1234'
    
    obj = mock.Mock()
    data = {'hi': 'there', 'blob': '...'}

    with mock.patch('storymarket.Storymarket') as mock_storymarket:
        with mock.patch.object(SyncedObject.objects, 'mark_synced') as mock_marked:
            utils.save_to_storymarket(obj, 'audio', data)
            
            # The call creates and API instance...
            mock_storymarket.assert_called_with(settings.STORYMARKET_API_KEY)
            
            # Calls that instance's text.create() method...
            mock_storymarket_instance = mock_storymarket.return_value
            mock_storymarket_instance.audio.create.assert_called_with({'hi': 'there'})
            
            # Uploads the blob using thr object returned by create()...
            create_rv = mock_storymarket_instance.audio.create.return_value
            create_rv.upload_blob.assert_called_with('...')
            
            # And calls mark_synced.
            mock_marked.assert_called_with(obj, create_rv)
            
            