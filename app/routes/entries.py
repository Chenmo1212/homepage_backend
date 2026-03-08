from flask import Blueprint, jsonify, request
from app.models.entry import Entry
from app.validators.schema_validator import validator
from app.config.type_manager import type_manager
from app.notifications.notification_service import send_notification

entries_bp = Blueprint('entries', __name__, url_prefix='/api/v1/entries')


@entries_bp.route('', methods=['GET'])
def get_entries():
    """获取entries列表"""
    try:
        # 获取查询参数
        type_filter = request.args.get('type')
        source_filter = request.args.get('source')
        is_show = request.args.get('is_show')
        tags = request.args.getlist('tags')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # 构建过滤条件
        filters = {}
        if type_filter:
            filters['type'] = type_filter
        if source_filter:
            filters['source'] = source_filter
        if is_show is not None:
            filters['status.is_show'] = is_show.lower() == 'true'
            filters['status.is_delete'] = False
        if tags:
            filters['tags'] = {'$in': tags}
        
        # 查询数据
        entries, total = Entry.find_all(filters, page, limit)
        
        # 格式化返回数据
        entry_list = []
        for entry in entries:
            entry_dict = {
                'id': str(entry['_id']),
                'type': entry['type'],
                'source': entry.get('source'),
                'metadata': entry['metadata'],
                'status': entry['status'],
                'timestamps': entry['timestamps'],
                'tags': entry.get('tags', [])
            }
            entry_list.append(entry_dict)
        
        return jsonify({
            'data': entry_list,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            },
            'status': 200
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500


@entries_bp.route('', methods=['POST'])
def create_entry():
    """创建新entry"""
    try:
        data = request.json
        
        # 验证必需字段
        if 'type' not in data or 'metadata' not in data:
            return jsonify({
                'error': 'Missing required fields: type and metadata',
                'status': 400
            }), 400
        
        entry_type = data['type']
        metadata = data['metadata']
        
        # 验证类型是否存在
        if not type_manager.type_exists(entry_type):
            return jsonify({
                'error': f'Unknown entry type: {entry_type}',
                'status': 400
            }), 400
        
        # 验证metadata
        is_valid, error_msg = validator.validate_entry(entry_type, metadata)
        if not is_valid:
            return jsonify({
                'error': f'Validation failed: {error_msg}',
                'status': 400
            }), 400
        
        # 创建entry
        entry = Entry(
            type=entry_type,
            metadata=metadata,
            source=data.get('source'),
            agent=data.get('agent', ''),
            tags=data.get('tags', [])
        )
        
        entry_id = entry.save()
        
        # 发送通知
        try:
            send_notification(entry_type, metadata, data.get('source'))
        except Exception as e:
            # 通知失败不影响entry创建
            print(f'Notification failed: {str(e)}')
        
        return jsonify({
            'msg': 'Entry created successfully',
            'data': {'id': entry_id},
            'status': 200
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500


@entries_bp.route('/<string:entry_id>', methods=['GET'])
def get_entry(entry_id):
    """获取单个entry"""
    try:
        entry = Entry.find_by_id(entry_id)
        
        if not entry:
            return jsonify({
                'error': 'Entry not found',
                'status': 404
            }), 404
        
        entry_dict = {
            'id': str(entry['_id']),
            'type': entry['type'],
            'source': entry.get('source'),
            'metadata': entry['metadata'],
            'status': entry['status'],
            'timestamps': entry['timestamps'],
            'tags': entry.get('tags', [])
        }
        
        return jsonify({'data': entry_dict, 'status': 200})
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500


@entries_bp.route('/<string:entry_id>', methods=['PUT'])
def update_entry(entry_id):
    """更新entry"""
    try:
        data = request.json
        entry = Entry.find_by_id(entry_id)
        
        if not entry:
            return jsonify({
                'error': 'Entry not found',
                'status': 404
            }), 404
        
        # 如果更新metadata，需要验证
        if 'metadata' in data:
            is_valid, error_msg = validator.validate_entry(
                entry['type'],
                data['metadata']
            )
            if not is_valid:
                return jsonify({
                    'error': f'Validation failed: {error_msg}',
                    'status': 400
                }), 400
        
        # 更新entry
        entry_obj = Entry(
            type=entry['type'],
            metadata=data.get('metadata', entry['metadata']),
            source=data.get('source', entry.get('source')),
            status=data.get('status', entry['status']),
            timestamps=entry['timestamps'],
            agent=data.get('agent', entry.get('agent')),
            tags=data.get('tags', entry.get('tags', [])),
            id=entry_id
        )
        
        entry_obj.save()
        
        return jsonify({
            'msg': 'Entry updated successfully',
            'status': 200
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500


@entries_bp.route('/<string:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    """删除entry"""
    try:
        entry = Entry.find_by_id(entry_id)
        
        if not entry:
            return jsonify({
                'error': 'Entry not found',
                'status': 404
            }), 404
        
        entry_obj = Entry(
            type=entry['type'],
            metadata=entry['metadata'],
            id=entry_id
        )
        entry_obj.delete()
        
        return jsonify({
            'msg': 'Entry deleted successfully',
            'status': 200
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500


@entries_bp.route('/batch-delete', methods=['POST'])
def batch_delete_entries():
    """批量删除entries"""
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
            'msg': f'Deleted {deleted_count} entries',
            'status': 200
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500

# Made with Bob
