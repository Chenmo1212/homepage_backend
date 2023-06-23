import pytest
from app import app  # Import your application's app object


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_get_message_list(client):
    response = client.get('/messages')
    assert response.status_code == 200
    assert 'data' in response.json


def test_admin_get_all_messages(client):
    payload = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'content': 'Hello, world!'
    }
    response = client.post('/messages', json=payload)
    assert response.status_code == 200
    assert 'msg' in response.json
    message_id = response.json['data']['id']

    # Get a list of all messages
    response = client.get('/admin/messages')
    assert response.status_code == 200
    assert 'data' in response.json

    # Verify that the newly added message is in the returned result
    data = response.json['data']
    new_message = next((msg for msg in data if msg['id'] == message_id), None)
    assert new_message is not None
    assert new_message['is_show'] is False


def test_get_all_message_list(client):
    response = client.get('/admin/messages')
    assert response.status_code == 200
    assert 'data' in response.json


@pytest.mark.parametrize("is_show, is_delete, modify_delete", [
    (True, False, False),  # Test case: is_show=True, is_delete=False, modify_delete=False
    (False, True, False),  # Test case: is_show=False, is_delete=True, modify_delete=False
    (True, True, True),    # Test case: is_show=True, is_delete=True, modify_delete=True
    (True, False, True),   # Test case: is_show=True, is_delete=False, modify_delete=True
    (False, True, True),   # Test case: is_show=False, is_delete=True, modify_delete=True
])
def test_update_message_status(client, is_show, is_delete, modify_delete):
    payload = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'content': 'Hello, world!'
    }
    response = client.post('/messages', json=payload)
    assert response.status_code == 200
    assert 'msg' in response.json
    message_id = response.json['data']['id']

    payload = {
        'is_show': is_show,
    }
    if modify_delete:
        payload['is_delete'] = is_delete

    response = client.put(f'/admin/messages/{message_id}/status', json=payload)
    assert response.status_code == 200
    assert 'msg' in response.json

    # Get the message list and verify the modification result
    response = client.get('/admin/messages')
    assert response.status_code == 200
    assert 'data' in response.json
    data = response.json['data']
    updated_message = next((msg for msg in data if msg['id'] == message_id), None)
    assert updated_message is not None
    assert updated_message['is_show'] == is_show
    if modify_delete:
        assert updated_message['is_delete'] == is_delete


def test_delete_messages(client):
    messages = [
        {
            'name': 'John Doe',
            'email': 'john@example.com',
            'content': 'Message 1'
        },
        {
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'content': 'Message 2'
        },
        {
            'name': 'Bob Johnson',
            'email': 'bob@example.com',
            'content': 'Message 3'
        }
    ]

    message_ids = []

    # Add a test message and record its ID
    for message in messages:
        response = client.post('/messages', json=message)
        assert response.status_code == 200
        assert 'msg' in response.json
        assert 'data' in response.json
        message_id = response.json['data']['id']
        message_ids.append(message_id)

    # delete message
    payload = {'id_list': message_ids}
    response = client.post('/admin/messages/delete', json=payload)
    assert response.status_code == 200
    assert 'msg' in response.json
    assert response.json['msg'] == f'Deleted {len(message_ids)} messages'

    # Verification message has been removed
    response = client.get('/admin/messages')
    assert response.status_code == 200
    assert 'data' in response.json
    data = response.json['data']
    # Check if there is a deleted message id
    for message_id in message_ids:
        assert not any(message['id'] == message_id for message in data)
