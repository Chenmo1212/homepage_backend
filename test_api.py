"""
Homepage Backend API Tests
Test aggregated API system and backward compatible messages endpoints
"""

import pytest
from app import app


@pytest.fixture
def client():
    """Create test client"""
    with app.test_client() as client:
        yield client


# ============================================================================
# Backward Compatibility Tests - Legacy Messages API
# ============================================================================

class TestLegacyMessagesAPI:
    """Test backward compatible messages endpoints"""
    
    def test_get_message_list(self, client):
        """Test getting visible message list"""
        response = client.get('/messages')
        assert response.status_code == 200
        assert 'data' in response.json
        assert 'status' in response.json
        assert response.json['status'] == 200
    
    def test_create_message(self, client):
        """Test creating a message"""
        payload = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'content': 'Hello, world!',
            'website': 'https://example.com'
        }
        response = client.post('/messages', json=payload)
        assert response.status_code == 200
        assert 'msg' in response.json
        assert 'data' in response.json
        assert 'id' in response.json['data']
    
    def test_create_message_missing_fields(self, client):
        """Test creating message with missing required fields"""
        payload = {
            'name': 'John Doe',
            # Missing email and content
        }
        response = client.post('/messages', json=payload)
        assert response.status_code == 400
        assert 'error' in response.json
    
    def test_admin_get_all_messages(self, client):
        """Test admin getting all messages"""
        # First create a message
        payload = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'content': 'Test message'
        }
        response = client.post('/messages', json=payload)
        assert response.status_code == 200
        message_id = response.json['data']['id']
        
        # Get all messages
        response = client.get('/admin/messages')
        assert response.status_code == 200
        assert 'data' in response.json
        
        # Verify newly created message is in the list
        data = response.json['data']
        new_message = next((msg for msg in data if msg['id'] == message_id), None)
        assert new_message is not None
        assert new_message['is_show'] is False  # Default not visible
    
    @pytest.mark.parametrize("is_show, is_delete, modify_delete", [
        (True, False, False),
        (False, True, False),
        (True, True, True),
        (True, False, True),
        (False, True, True),
    ])
    def test_update_message_status(self, client, is_show, is_delete, modify_delete):
        """Test updating message status"""
        # Create message
        payload = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'content': 'Test message'
        }
        response = client.post('/messages', json=payload)
        assert response.status_code == 200
        message_id = response.json['data']['id']
        
        # Update status
        update_payload = {'is_show': is_show}
        if modify_delete:
            update_payload['is_delete'] = is_delete
        
        response = client.put(f'/admin/messages/{message_id}/status', json=update_payload)
        assert response.status_code == 200
        assert 'msg' in response.json
        
        # Verify update result
        response = client.get('/admin/messages')
        assert response.status_code == 200
        data = response.json['data']
        updated_message = next((msg for msg in data if msg['id'] == message_id), None)
        assert updated_message is not None
        assert updated_message['is_show'] == is_show
        if modify_delete:
            assert updated_message['is_delete'] == is_delete
    
    def test_delete_messages(self, client):
        """Test batch deleting messages"""
        messages = [
            {'name': 'User1', 'email': 'user1@example.com', 'content': 'Message 1'},
            {'name': 'User2', 'email': 'user2@example.com', 'content': 'Message 2'},
            {'name': 'User3', 'email': 'user3@example.com', 'content': 'Message 3'}
        ]
        
        message_ids = []
        for message in messages:
            response = client.post('/messages', json=message)
            assert response.status_code == 200
            message_ids.append(response.json['data']['id'])
        
        # Batch delete
        response = client.post('/admin/messages/delete', json={'id_list': message_ids})
        assert response.status_code == 200
        assert 'msg' in response.json
        
        # Verify deleted
        response = client.get('/admin/messages')
        assert response.status_code == 200
        data = response.json['data']
        for message_id in message_ids:
            assert not any(msg['id'] == message_id for msg in data)


# ============================================================================
# New Aggregated API Tests - Entries API v1
# ============================================================================

class TestEntriesAPI:
    """Test new aggregated API endpoints"""
    
    def test_create_message_entry(self, client):
        """Test creating message type entry via new API"""
        payload = {
            'type': 'message',
            'source': 'homepage',
            'metadata': {
                'name': 'Test User',
                'email': 'test@example.com',
                'content': 'Test message via new API',
                'website': 'https://test.com'
            }
        }
        response = client.post('/api/v1/entries', json=payload)
        assert response.status_code == 200
        assert 'data' in response.json
        assert 'id' in response.json['data']
    
    def test_create_feedback_entry(self, client):
        """Test creating feedback type entry"""
        payload = {
            'type': 'feedback',
            'source': 'homepage',
            'metadata': {
                'project_name': 'Test Project',
                'title': 'Feature Request',
                'content': 'Please add dark mode',
                'category': 'feature',
                'rating': 5,
                'contact': 'user@example.com'
            }
        }
        response = client.post('/api/v1/entries', json=payload)
        assert response.status_code == 200
        assert 'data' in response.json
        assert 'id' in response.json['data']
    
    def test_create_notification_entry(self, client):
        """Test creating notification type entry"""
        payload = {
            'type': 'notification',
            'source': 'system',
            'metadata': {
                'title': 'System Maintenance',
                'content': 'System will be down for maintenance',
                'level': 'warning',
                'target_users': ['admin']
            }
        }
        response = client.post('/api/v1/entries', json=payload)
        assert response.status_code == 200
        assert 'data' in response.json
        assert 'id' in response.json['data']
    
    def test_create_entry_invalid_type(self, client):
        """Test creating entry with invalid type"""
        payload = {
            'type': 'invalid_type',
            'source': 'test',
            'metadata': {}
        }
        response = client.post('/api/v1/entries', json=payload)
        assert response.status_code == 400
        assert 'error' in response.json
    
    def test_create_entry_missing_required_fields(self, client):
        """Test creating entry with missing required fields"""
        payload = {
            'type': 'feedback',
            'source': 'homepage',
            'metadata': {
                'title': 'Test',
                # Missing project_name, content, category
            }
        }
        response = client.post('/api/v1/entries', json=payload)
        assert response.status_code == 400
        assert 'error' in response.json
    
    def test_get_visible_entries(self, client):
        """Test getting visible entries"""
        response = client.get('/api/v1/entries')
        assert response.status_code == 200
        assert 'data' in response.json
        assert 'pagination' in response.json
    
    def test_get_entries_filter_by_type(self, client):
        """Test filtering entries by type"""
        # Create entries of different types
        client.post('/api/v1/entries', json={
            'type': 'message',
            'source': 'test',
            'metadata': {'name': 'User', 'email': 'user@test.com', 'content': 'Test'}
        })
        client.post('/api/v1/entries', json={
            'type': 'feedback',
            'source': 'test',
            'metadata': {
                'project_name': 'Test', 'title': 'Test', 
                'content': 'Test', 'category': 'bug'
            }
        })
        
        # Filter by type
        response = client.get('/api/v1/entries?type=message')
        assert response.status_code == 200
        # Note: May return empty list due to default is_show=False
        assert 'data' in response.json
    
    def test_get_entries_filter_by_source(self, client):
        """Test filtering entries by source"""
        response = client.get('/api/v1/entries?source=homepage')
        assert response.status_code == 200
        assert 'data' in response.json
    
    def test_get_entries_pagination(self, client):
        """Test pagination functionality"""
        response = client.get('/api/v1/entries?page=1&limit=10')
        assert response.status_code == 200
        assert 'pagination' in response.json
        pagination = response.json['pagination']
        assert 'page' in pagination
        assert 'limit' in pagination
        assert 'total' in pagination


class TestAdminEntriesAPI:
    """Test admin API endpoints"""
    
    def test_get_all_entries(self, client):
        """Test getting all entries (including hidden ones)"""
        response = client.get('/api/v1/admin/entries')
        assert response.status_code == 200
        assert 'data' in response.json
        assert 'pagination' in response.json
    
    def test_get_entries_filter_by_type(self, client):
        """Test admin filtering by type"""
        response = client.get('/api/v1/admin/entries?type=message')
        assert response.status_code == 200
        assert 'data' in response.json
    
    def test_update_entry_status(self, client):
        """Test updating entry status"""
        # Create entry
        payload = {
            'type': 'message',
            'source': 'test',
            'metadata': {
                'name': 'Test',
                'email': 'test@test.com',
                'content': 'Test'
            }
        }
        response = client.post('/api/v1/entries', json=payload)
        assert response.status_code == 200
        entry_id = response.json['data']['id']
        
        # Update status
        update_payload = {
            'is_show': True,
            'is_read': True
        }
        response = client.put(f'/api/v1/admin/entries/{entry_id}/status', json=update_payload)
        assert response.status_code == 200
        assert 'msg' in response.json
    
    def test_get_entry_stats(self, client):
        """Test getting statistics"""
        response = client.get('/api/v1/admin/entries/stats')
        assert response.status_code == 200
        assert 'total' in response.json
        assert 'by_type' in response.json
        assert 'by_source' in response.json
        assert 'by_status' in response.json
    
    def test_get_all_types(self, client):
        """Test getting all supported types"""
        response = client.get('/api/v1/admin/types')
        assert response.status_code == 200
        assert 'types' in response.json
        types = response.json['types']
        assert 'message' in types
        assert 'feedback' in types
        assert 'notification' in types
    
    def test_get_type_schema(self, client):
        """Test getting type schema"""
        response = client.get('/api/v1/admin/types/message/schema')
        assert response.status_code == 200
        assert 'type' in response.json
        assert 'schema' in response.json
        assert response.json['type'] == 'message'
    
    def test_batch_delete_entries(self, client):
        """Test batch deleting entries"""
        # Create multiple entries
        entry_ids = []
        for i in range(3):
            response = client.post('/api/v1/entries', json={
                'type': 'message',
                'source': 'test',
                'metadata': {
                    'name': f'User{i}',
                    'email': f'user{i}@test.com',
                    'content': f'Test {i}'
                }
            })
            assert response.status_code == 200
            entry_ids.append(response.json['data']['id'])
        
        # Batch delete
        response = client.post('/api/v1/entries/batch-delete', json={'id_list': entry_ids})
        assert response.status_code == 200
        assert 'msg' in response.json


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Test system integration and backward compatibility"""
    
    def test_backward_compatibility(self, client):
        """Test backward compatibility: create via old API, query via new API"""
        # Create via old API
        payload = {
            'name': 'Test User',
            'email': 'test@example.com',
            'content': 'Test backward compatibility'
        }
        response = client.post('/messages', json=payload)
        assert response.status_code == 200
        message_id = response.json['data']['id']
        
        # Query via new API (admin endpoint)
        response = client.get('/api/v1/admin/entries?type=message')
        assert response.status_code == 200
        data = response.json['data']
        
        # Verify newly created message can be found
        found = any(entry['id'] == message_id for entry in data)
        assert found
    
    def test_cross_api_status_update(self, client):
        """Test cross-API status update: create via new API, update via old API"""
        # Create via new API
        payload = {
            'type': 'message',
            'source': 'homepage',
            'metadata': {
                'name': 'Test',
                'email': 'test@test.com',
                'content': 'Test'
            }
        }
        response = client.post('/api/v1/entries', json=payload)
        assert response.status_code == 200
        entry_id = response.json['data']['id']
        
        # Update status via old API
        response = client.put(f'/admin/messages/{entry_id}/status', json={'is_show': True})
        assert response.status_code == 200
        
        # Verify update succeeded
        response = client.get('/api/v1/admin/entries')
        assert response.status_code == 200
        data = response.json['data']
        updated_entry = next((e for e in data if e['id'] == entry_id), None)
        assert updated_entry is not None
        assert updated_entry['status']['is_show'] is True
    
    def test_multi_type_workflow(self, client):
        """Test multi-type workflow"""
        # Create entries of different types
        types_data = [
            {
                'type': 'message',
                'source': 'homepage',
                'metadata': {'name': 'User', 'email': 'user@test.com', 'content': 'Hello'}
            },
            {
                'type': 'feedback',
                'source': 'project_a',
                'metadata': {
                    'project_name': 'Project A',
                    'title': 'Bug Report',
                    'content': 'Found a bug',
                    'category': 'bug',
                    'rating': 3
                }
            },
            {
                'type': 'notification',
                'source': 'system',
                'metadata': {
                    'title': 'Update',
                    'content': 'New version available',
                    'level': 'info'
                }
            }
        ]
        
        created_ids = []
        for data in types_data:
            response = client.post('/api/v1/entries', json=data)
            assert response.status_code == 200
            created_ids.append(response.json['data']['id'])
        
        # Verify all types were created successfully
        response = client.get('/api/v1/admin/entries')
        assert response.status_code == 200
        all_entries = response.json['data']
        
        for entry_id in created_ids:
            found = any(e['id'] == entry_id for e in all_entries)
            assert found


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

# Made with Bob
