"""
Homepage Backend API Tests
测试聚合API系统和向后兼容的messages端点
"""

import pytest
from app import app


@pytest.fixture
def client():
    """创建测试客户端"""
    with app.test_client() as client:
        yield client


# ============================================================================
# 向后兼容测试 - Legacy Messages API
# ============================================================================

class TestLegacyMessagesAPI:
    """测试向后兼容的messages端点"""
    
    def test_get_message_list(self, client):
        """测试获取可见留言列表"""
        response = client.get('/messages')
        assert response.status_code == 200
        assert 'data' in response.json
        assert 'status' in response.json
        assert response.json['status'] == 200
    
    def test_create_message(self, client):
        """测试创建留言"""
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
        """测试创建留言时缺少必需字段"""
        payload = {
            'name': 'John Doe',
            # 缺少 email 和 content
        }
        response = client.post('/messages', json=payload)
        assert response.status_code == 400
        assert 'error' in response.json
    
    def test_admin_get_all_messages(self, client):
        """测试管理员获取所有留言"""
        # 先创建一条留言
        payload = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'content': 'Test message'
        }
        response = client.post('/messages', json=payload)
        assert response.status_code == 200
        message_id = response.json['data']['id']
        
        # 获取所有留言
        response = client.get('/admin/messages')
        assert response.status_code == 200
        assert 'data' in response.json
        
        # 验证新创建的留言在列表中
        data = response.json['data']
        new_message = next((msg for msg in data if msg['id'] == message_id), None)
        assert new_message is not None
        assert new_message['is_show'] is False  # 默认不可见
    
    @pytest.mark.parametrize("is_show, is_delete, modify_delete", [
        (True, False, False),
        (False, True, False),
        (True, True, True),
        (True, False, True),
        (False, True, True),
    ])
    def test_update_message_status(self, client, is_show, is_delete, modify_delete):
        """测试更新留言状态"""
        # 创建留言
        payload = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'content': 'Test message'
        }
        response = client.post('/messages', json=payload)
        assert response.status_code == 200
        message_id = response.json['data']['id']
        
        # 更新状态
        update_payload = {'is_show': is_show}
        if modify_delete:
            update_payload['is_delete'] = is_delete
        
        response = client.put(f'/admin/messages/{message_id}/status', json=update_payload)
        assert response.status_code == 200
        assert 'msg' in response.json
        
        # 验证更新结果
        response = client.get('/admin/messages')
        assert response.status_code == 200
        data = response.json['data']
        updated_message = next((msg for msg in data if msg['id'] == message_id), None)
        assert updated_message is not None
        assert updated_message['is_show'] == is_show
        if modify_delete:
            assert updated_message['is_delete'] == is_delete
    
    def test_delete_messages(self, client):
        """测试批量删除留言"""
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
        
        # 批量删除
        response = client.post('/admin/messages/delete', json={'id_list': message_ids})
        assert response.status_code == 200
        assert 'msg' in response.json
        
        # 验证已删除
        response = client.get('/admin/messages')
        assert response.status_code == 200
        data = response.json['data']
        for message_id in message_ids:
            assert not any(msg['id'] == message_id for msg in data)


# ============================================================================
# 新版聚合API测试 - Entries API v1
# ============================================================================

class TestEntriesAPI:
    """测试新版聚合API端点"""
    
    def test_create_message_entry(self, client):
        """测试通过新API创建message类型entry"""
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
        """测试创建feedback类型entry"""
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
        """测试创建notification类型entry"""
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
        """测试创建无效类型的entry"""
        payload = {
            'type': 'invalid_type',
            'source': 'test',
            'metadata': {}
        }
        response = client.post('/api/v1/entries', json=payload)
        assert response.status_code == 400
        assert 'error' in response.json
    
    def test_create_entry_missing_required_fields(self, client):
        """测试创建entry时缺少必需字段"""
        payload = {
            'type': 'feedback',
            'source': 'homepage',
            'metadata': {
                'title': 'Test',
                # 缺少 project_name, content, category
            }
        }
        response = client.post('/api/v1/entries', json=payload)
        assert response.status_code == 400
        assert 'error' in response.json
    
    def test_get_visible_entries(self, client):
        """测试获取可见entries"""
        response = client.get('/api/v1/entries')
        assert response.status_code == 200
        assert 'data' in response.json
        assert 'pagination' in response.json
    
    def test_get_entries_filter_by_type(self, client):
        """测试按类型过滤entries"""
        # 创建不同类型的entries
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
        
        # 按类型过滤
        response = client.get('/api/v1/entries?type=message')
        assert response.status_code == 200
        # 注意：由于默认is_show=False，可能返回空列表
        assert 'data' in response.json
    
    def test_get_entries_filter_by_source(self, client):
        """测试按来源过滤entries"""
        response = client.get('/api/v1/entries?source=homepage')
        assert response.status_code == 200
        assert 'data' in response.json
    
    def test_get_entries_pagination(self, client):
        """测试分页功能"""
        response = client.get('/api/v1/entries?page=1&limit=10')
        assert response.status_code == 200
        assert 'pagination' in response.json
        pagination = response.json['pagination']
        assert 'page' in pagination
        assert 'limit' in pagination
        assert 'total' in pagination


class TestAdminEntriesAPI:
    """测试管理员API端点"""
    
    def test_get_all_entries(self, client):
        """测试获取所有entries（包括隐藏的）"""
        response = client.get('/api/v1/admin/entries')
        assert response.status_code == 200
        assert 'data' in response.json
        assert 'pagination' in response.json
    
    def test_get_entries_filter_by_type(self, client):
        """测试管理员按类型过滤"""
        response = client.get('/api/v1/admin/entries?type=message')
        assert response.status_code == 200
        assert 'data' in response.json
    
    def test_update_entry_status(self, client):
        """测试更新entry状态"""
        # 创建entry
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
        
        # 更新状态
        update_payload = {
            'is_show': True,
            'is_read': True
        }
        response = client.put(f'/api/v1/admin/entries/{entry_id}/status', json=update_payload)
        assert response.status_code == 200
        assert 'msg' in response.json
    
    def test_get_entry_stats(self, client):
        """测试获取统计信息"""
        response = client.get('/api/v1/admin/entries/stats')
        assert response.status_code == 200
        assert 'total' in response.json
        assert 'by_type' in response.json
        assert 'by_source' in response.json
        assert 'by_status' in response.json
    
    def test_get_all_types(self, client):
        """测试获取所有支持的类型"""
        response = client.get('/api/v1/admin/types')
        assert response.status_code == 200
        assert 'types' in response.json
        types = response.json['types']
        assert 'message' in types
        assert 'feedback' in types
        assert 'notification' in types
    
    def test_get_type_schema(self, client):
        """测试获取类型schema"""
        response = client.get('/api/v1/admin/types/message/schema')
        assert response.status_code == 200
        assert 'type' in response.json
        assert 'schema' in response.json
        assert response.json['type'] == 'message'
    
    def test_batch_delete_entries(self, client):
        """测试批量删除entries"""
        # 创建多个entries
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
        
        # 批量删除
        response = client.post('/api/v1/entries/batch-delete', json={'id_list': entry_ids})
        assert response.status_code == 200
        assert 'msg' in response.json


# ============================================================================
# 集成测试
# ============================================================================

class TestIntegration:
    """测试系统集成和向后兼容性"""
    
    def test_backward_compatibility(self, client):
        """测试向后兼容性：通过旧API创建，通过新API查询"""
        # 通过旧API创建message
        payload = {
            'name': 'Test User',
            'email': 'test@example.com',
            'content': 'Test backward compatibility'
        }
        response = client.post('/messages', json=payload)
        assert response.status_code == 200
        message_id = response.json['data']['id']
        
        # 通过新API查询（管理员端点）
        response = client.get('/api/v1/admin/entries?type=message')
        assert response.status_code == 200
        data = response.json['data']
        
        # 验证能找到刚创建的message
        found = any(entry['id'] == message_id for entry in data)
        assert found
    
    def test_cross_api_status_update(self, client):
        """测试跨API状态更新：新API创建，旧API更新"""
        # 通过新API创建
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
        
        # 通过旧API更新状态
        response = client.put(f'/admin/messages/{entry_id}/status', json={'is_show': True})
        assert response.status_code == 200
        
        # 验证更新成功
        response = client.get('/api/v1/admin/entries')
        assert response.status_code == 200
        data = response.json['data']
        updated_entry = next((e for e in data if e['id'] == entry_id), None)
        assert updated_entry is not None
        assert updated_entry['status']['is_show'] is True
    
    def test_multi_type_workflow(self, client):
        """测试多类型工作流"""
        # 创建不同类型的entries
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
        
        # 验证所有类型都创建成功
        response = client.get('/api/v1/admin/entries')
        assert response.status_code == 200
        all_entries = response.json['data']
        
        for entry_id in created_ids:
            found = any(e['id'] == entry_id for e in all_entries)
            assert found


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

# Made with Bob
