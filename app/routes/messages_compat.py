from flask import Blueprint, jsonify, request
from app.models.entry import Entry
from app.validators.schema_validator import validator
from app.notifications.notification_service import send_notification

messages_compat_bp = Blueprint('messages_compat', __name__)


@messages_compat_bp.route('/messages', methods=['GET'])
def get_messages():
    """向后兼容：获取可见的messages"""
    try:
        entries = Entry.find_visible(type='message')
        
        message_list = []
        for entry in entries:
            message_dict = {
                'id': str(entry['_id']),
                'name': entry['metadata'].get('name'),
                'email': entry['metadata'].get('email'),
                'content': entry['metadata'].get('content'),
                'create_time': entry['timestamps']['create_time']
            }
            message_list.append(message_dict)
        
        return jsonify({'data': message_list, 'status': 200})
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500


@messages_compat_bp.route('/messages', methods=['POST'])
def create_message():
    """向后兼容：创建新message"""
    try:
        data = request.json
        
        required_fields = ['name', 'email', 'content']
        metadata = {field: data.get(field, '') for field in required_fields}
        metadata['website'] = data.get('website', '')
        
        if not all(metadata[field] for field in required_fields):
            return jsonify({
                'error': 'Missing required fields',
                'status': 400
            }), 400
        
        # 验证metadata
        is_valid, error_msg = validator.validate_entry('message', metadata)
        if not is_valid:
            return jsonify({
                'error': f'Validation failed: {error_msg}',
                'status': 400
            }), 400
        
        # 创建entry
        entry = Entry(
            type='message',
            metadata=metadata,
            source='homepage',
            agent=data.get('agent', '')
        )
        
        entry_id = entry.save()
        
        # 发送通知
        try:
            send_notification('message', metadata, 'homepage')
        except Exception as e:
            print(f'Notification failed: {str(e)}')
        
        return jsonify({
            'msg': 'Message created successfully',
            'data': {'id': entry_id},
            'status': 200
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500


@messages_compat_bp.route('/admin/messages', methods=['GET'])
def get_all_messages():
    """向后兼容：管理员获取所有messages"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 100))
        
        filters = {'type': 'message'}
        entries, total = Entry.find_all(filters, page, limit)
        
        message_list = []
        for entry in entries:
            message_dict = {
                'id': str(entry['_id']),
                'name': entry['metadata'].get('name'),
                'email': entry['metadata'].get('email'),
                'website': entry['metadata'].get('website', ''),
                'content': entry['metadata'].get('content'),
                'agent': entry.get('agent', ''),
                'create_time': entry['timestamps']['create_time'],
                'update_time': entry['timestamps']['update_time'],
                'admin_time': entry['timestamps']['admin_time'],
                'delete_time': entry['timestamps'].get('delete_time'),
                'is_delete': entry['status']['is_delete'],
                'is_show': entry['status']['is_show']
            }
            message_list.append(message_dict)
        
        return jsonify({'data': message_list, 'status': 200})
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500


@messages_compat_bp.route('/admin/messages/<string:message_id>/status', methods=['PUT'])
def update_message_status(message_id):
    """向后兼容：更新message状态"""
    try:
        data = request.json
        
        if not data:
            return jsonify({
                'error': 'No data provided',
                'status': 400
            }), 400
        
        # 更新状态
        success = Entry.update_status(message_id, data)
        
        if success:
            # 构建响应消息
            update_msg = ""
            if 'is_show' in data:
                update_msg += f"is_show changed to {data['is_show']}, "
            if 'is_delete' in data:
                update_msg += f"is_delete changed to {data['is_delete']}, "
            
            response_msg = 'Message updated successfully'
            if update_msg:
                response_msg += ' (' + update_msg.rstrip(', ') + ')'
            
            return jsonify({
                'msg': response_msg,
                'status': 200
            })
        else:
            return jsonify({
                'error': 'No document found to update',
                'status': 404
            }), 404
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500


@messages_compat_bp.route('/admin/messages/<string:message_id>', methods=['DELETE'])
def delete_message(message_id):
    """向后兼容：删除message"""
    try:
        entry = Entry.find_by_id(message_id)
        
        if not entry:
            return jsonify({
                'msg': 'No item found to delete',
                'status': 404
            }), 404
        
        entry_obj = Entry(
            type=entry['type'],
            metadata=entry['metadata'],
            id=message_id
        )
        entry_obj.delete()
        
        return jsonify({
            'msg': 'Item deleted successfully',
            'status': 200
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500


@messages_compat_bp.route('/admin/messages/delete', methods=['POST'])
def delete_many_messages():
    """向后兼容：批量删除messages"""
    try:
        data = request.json
        id_list = data.get('id_list', [])
        
        if not id_list:
            return jsonify({
                'error': 'Missing id_list field',
                'status': 400
            }), 400
        
        deleted_count = Entry.delete_many(id_list)
        
        return jsonify({
            'msg': f'Deleted {deleted_count} messages',
            'status': 200
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500

# Made with Bob
