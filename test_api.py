"""
Homepage Backend API Tests
Test aggregated API system with mocked MongoDB

使用 mongomock 模拟 MongoDB，无需真实数据库即可运行测试
所有的 fixtures 都在 conftest.py 中定义
"""

import pytest


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
        response = client.post('/api/v1/message/entries', json=payload)
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
        response = client.post('/api/v1/message/entries', json=payload)
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
        response = client.post('/api/v1/message/entries', json=payload)
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
        response = client.post('/api/v1/message/entries', json=payload)
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
        response = client.post('/api/v1/message/entries', json=payload)
        assert response.status_code == 400
        assert 'error' in response.json
    
    def test_get_visible_entries(self, client):
        """Test getting visible entries"""
        response = client.get('/api/v1/message/entries')
        assert response.status_code == 200
        assert 'data' in response.json
        assert 'pagination' in response.json
    
    def test_get_entries_filter_by_type(self, client):
        """Test filtering entries by type"""
        # Create entries of different types
        client.post('/api/v1/message/entries', json={
            'type': 'message',
            'source': 'test',
            'metadata': {'name': 'User', 'email': 'user@test.com', 'content': 'Test'}
        })
        client.post('/api/v1/message/entries', json={
            'type': 'feedback',
            'source': 'test',
            'metadata': {
                'project_name': 'Test', 'title': 'Test', 
                'content': 'Test', 'category': 'bug'
            }
        })
        
        # Filter by type
        response = client.get('/api/v1/message/entries?type=message')
        assert response.status_code == 200
        # Note: May return empty list due to default is_show=False
        assert 'data' in response.json
    
    def test_get_entries_filter_by_source(self, client):
        """Test filtering entries by source"""
        response = client.get('/api/v1/message/entries?source=homepage')
        assert response.status_code == 200
        assert 'data' in response.json
    
    def test_get_entries_pagination(self, client):
        """Test pagination functionality"""
        response = client.get('/api/v1/message/entries?page=1&limit=10')
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
        response = client.get('/api/v1/message/admin/entries')
        assert response.status_code == 200
        assert 'data' in response.json
        assert 'pagination' in response.json
    
    def test_get_entries_filter_by_type(self, client):
        """Test admin filtering by type"""
        response = client.get('/api/v1/message/admin/entries?type=message')
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
        response = client.post('/api/v1/message/entries', json=payload)
        assert response.status_code == 200
        entry_id = response.json['data']['id']
        
        # Update status
        update_payload = {
            'is_show': True,
            'is_read': True
        }
        response = client.put(f'/api/v1/message/admin/entries/{entry_id}/status', json=update_payload)
        assert response.status_code == 200
        assert 'msg' in response.json
    
    def test_get_entry_stats(self, client):
        """Test getting statistics"""
        response = client.get('/api/v1/message/admin/entries/stats')
        assert response.status_code == 200
        data = response.json['data']
        assert 'total' in data
        assert 'by_type' in data
    
    def test_get_all_types(self, client):
        """Test getting all supported types"""
        response = client.get('/api/v1/message/admin/types')
        assert response.status_code == 200
        types_list = response.json['data']
        assert isinstance(types_list, list)
        type_names = [t['type'] for t in types_list]
        assert 'message' in type_names
        assert 'feedback' in type_names
        assert 'notification' in type_names
    
    def test_get_type_schema(self, client):
        """Test getting type schema"""
        response = client.get('/api/v1/message/admin/types/message/schema')
        assert response.status_code == 200
        data = response.json['data']
        assert 'schema' in data
        assert 'name' in data
        assert 'description' in data
    
    def test_batch_delete_entries(self, client):
        """Test batch deleting entries"""
        # Create multiple entries
        entry_ids = []
        for i in range(3):
            response = client.post('/api/v1/message/entries', json={
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
        response = client.post('/api/v1/message/entries/batch-delete', json={'id_list': entry_ids})
        assert response.status_code == 200
        assert 'msg' in response.json


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Test system integration"""
    
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
            response = client.post('/api/v1/message/entries', json=data)
            assert response.status_code == 200
            created_ids.append(response.json['data']['id'])
        
        # Verify all types were created successfully
        response = client.get('/api/v1/message/admin/entries')
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
