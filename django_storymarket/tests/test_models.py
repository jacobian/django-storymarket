import mock
import datetime
from contextlib import nested
from django.contrib.contenttypes.models import ContentType
from django_storymarket.models import SyncedObject
    
def test_mark_synced():
    mock_sm_obj = mock.Mock()
    mock_django_obj = mock.Mock()

    mock_ct = mock.Mock()
    mock_get_for_model = mock.Mock(return_value=mock_ct)
    ct_patch = mock.patch.object(ContentType.objects, 'get_for_model', mock_get_for_model)
    
    mock_synced_obj = mock.Mock()
    mock_get_or_create = mock.Mock(return_value=(mock_synced_obj, True))
    get_or_create_patch = mock.patch.object(SyncedObject.objects, 'get_or_create', mock_get_or_create)
    
    with nested(ct_patch, get_or_create_patch):
        SyncedObject.objects.mark_synced(mock_django_obj, mock_sm_obj)
        assert mock_get_or_create.called
    
    # Now try with an existing object
    mock_get_or_create.return_value = (mock_synced_obj, False)
    with nested(ct_patch, get_or_create_patch):
        SyncedObject.objects.mark_synced(mock_django_obj, mock_sm_obj)
        assert mock_synced_obj.save.called
    
