import mock
import contextlib
import unittest
import storymarket
from django.conf import settings
from django_storymarket import utils
from django_storymarket.models import SyncedObject

def setup():
    utils.QUEUE_UPLOADS = False
    settings.STORYMARKET_API_KEY = '1234'

def patch_storymarket():
    mock_api = mock.Mock()
    mock_api.return_value = mock.Mock(spec=storymarket.Storymarket(''))
    return contextlib.nested(
        mock.patch('storymarket.Storymarket', new=mock_api),
        mock.patch.object(SyncedObject.objects, 'mark_synced'),
    )

def test_save_to_storymarket():
    obj = mock.Mock()
    data = {'hi': 'there', 'blob': '...'}

    with patch_storymarket() as (mock_api, mock_marked):
        utils.save_to_storymarket(obj, 'audio', data)
        
        # The call creates and API instance...
        mock_api.assert_called_with(settings.STORYMARKET_API_KEY)
        
        # Calls that instance's text.create() method...
        sm = mock_api.return_value
        sm.audio.create.assert_called_with({'hi': 'there'})
        
        # Uploads the blob using thr object returned by create()...
        create_rv = sm.audio.create.return_value
        create_rv.upload_blob.assert_called_with('...')
        
        # And calls mark_synced.
        mock_marked.assert_called_with(obj, create_rv)
            
def test_package_saving():
    obj1 = mock.Mock()
    obj2 = mock.Mock()
    obj3 = mock.Mock()
    data = {'items': [{'type': 'photo', 'object': obj2, 'foo': 'bar'},
                      {'type': 'video', 'object': obj3, 'foo': 'baz'}]}
                      
    with patch_storymarket() as (mock_api, mock_marked):
        utils.save_to_storymarket(obj1, 'package', data)
        
        sm = mock_api.return_value
        sm.photos.create.assert_called_with({'foo': 'bar'})
        sm.video.create.assert_called_with({'foo': 'baz'})
        
        sm.packages.create.assert_called_with({
            'photo_items': [mock_marked.return_value.storymarket_id],
            'video_items': [mock_marked.return_value.storymarket_id]
        })