from flask import Blueprint, jsonify, request
from app.models.entry import Entry
from app.config.type_manager import type_manager
from app.validators.schema_validator import validator

admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')


@admin_bp.route('/entries', methods=['GET'])
def get_all_entries():
    """管理员获取所有entries"""
    try:
        # 获取查询参数
        type_filter = request.args.get('type')
        source_filter = request.args.get('source')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # 构建过滤条件
        filters = {}
        if type_filter:
            filters['type'] = type_filter
        if source_filter:
            filters['source'] = source_filter
        
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
                'agent': entry.get('agent', ''),
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


@admin_bp.route('/entries/<string:entry_id>/status', methods=['PUT'])
def update_entry_status(entry_id):
    """更新entry状态"""
    try:
        data = request.json
        
        if not data:
            return jsonify({
                'error': 'No data provided',
                'status': 400
            }), 400
        
        # 更新状态
        success = Entry.update_status(entry_id, data)
        
        if success:
            return jsonify({
                'msg': 'Entry status updated successfully',
                'status': 200
            })
        else:
            return jsonify({
                'error': 'Entry not found or no valid fields to update',
                'status': 404
            }), 404
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500


@admin_bp.route('/entries/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    try:
        # 获取过滤参数
        type_filter = request.args.get('type')
        source_filter = request.args.get('source')
        
        filters = {}
        if type_filter:
            filters['type'] = type_filter
        if source_filter:
            filters['source'] = source_filter
        
        stats = Entry.get_stats(filters)
        
        return jsonify({
            'data': stats,
            'status': 200
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500


@admin_bp.route('/types', methods=['GET'])
def get_types():
    """获取所有支持的类型"""
    try:
        types = type_manager.get_all_types()
        
        # 格式化返回数据，不包含完整schema
        type_list = []
        for type_name, config in types.items():
            type_info = {
                'type': type_name,
                'name': config.get('name'),
                'description': config.get('description'),
                'notification_enabled': config.get('notification', {}).get('enabled', False)
            }
            type_list.append(type_info)
        
        return jsonify({
            'data': type_list,
            'status': 200
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500


@admin_bp.route('/types/<string:type_name>/schema', methods=['GET'])
def get_type_schema(type_name):
    """获取特定类型的schema"""
    try:
        type_config = type_manager.get_type(type_name)
        
        if not type_config:
            return jsonify({
                'error': f'Type not found: {type_name}',
                'status': 404
            }), 404
        
        return jsonify({
            'data': type_config,
            'status': 200
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500


@admin_bp.route('/types', methods=['POST'])
def create_type():
    """创建新类型"""
    try:
        data = request.json
        
        if 'type' not in data or 'config' not in data:
            return jsonify({
                'error': 'Missing required fields: type and config',
                'status': 400
            }), 400
        
        type_name = data['type']
        config = data['config']
        
        # 验证配置
        is_valid, error_msg = validator.validate_type_config(config)
        if not is_valid:
            return jsonify({
                'error': f'Invalid type config: {error_msg}',
                'status': 400
            }), 400
        
        # 添加类型
        success = type_manager.add_type(type_name, config)
        
        if success:
            return jsonify({
                'msg': f'Type {type_name} created successfully',
                'status': 200
            })
        else:
            return jsonify({
                'error': f'Type {type_name} already exists',
                'status': 400
            }), 400
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500


@admin_bp.route('/types/<string:type_name>', methods=['PUT'])
def update_type(type_name):
    """更新类型配置"""
    try:
        data = request.json
        
        if 'config' not in data:
            return jsonify({
                'error': 'Missing required field: config',
                'status': 400
            }), 400
        
        config = data['config']
        
        # 验证配置
        is_valid, error_msg = validator.validate_type_config(config)
        if not is_valid:
            return jsonify({
                'error': f'Invalid type config: {error_msg}',
                'status': 400
            }), 400
        
        # 更新类型
        success = type_manager.update_type(type_name, config)
        
        if success:
            return jsonify({
                'msg': f'Type {type_name} updated successfully',
                'status': 200
            })
        else:
            return jsonify({
                'error': f'Type {type_name} not found',
                'status': 404
            }), 404
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 500}), 500

# Made with Bob
