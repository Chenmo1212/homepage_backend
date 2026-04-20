from flask import Blueprint, jsonify, request
from app.modules.homepage.models.entry import Entry
from app.modules.homepage.validators.schema_validator import validator
from app.modules.homepage.config.type_manager import type_manager
from app.modules.homepage.notifications.notification_service import send_notification

entries_bp = Blueprint('entries', __name__, url_prefix='/api/v1/message/entries')


@entries_bp.route('', methods=['GET'])
def get_entries():
    """Get entries list"""
    try:
        # Get query parameters
        type_filter = request.args.get('type')
        source_filter = request.args.get('source')
        is_show = request.args.get('is_show')
        tags = request.args.getlist('tags')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # Build filter conditions
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
        
        # Query data
        entries, total = Entry.find_all(filters, page, limit)
        
        # Format return data
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
    """Create new entry"""
    try:
        data = request.json
        
        # Validate required fields
        if 'type' not in data or 'metadata' not in data:
            return jsonify({
                'error': 'Missing required fields: type and metadata',
                'status': 400
            }), 400
        
        entry_type = data['type']
        metadata = data['metadata']
        
        # Validate if type exists
        if not type_manager.type_exists(entry_type):
            return jsonify({
                'error': f'Unknown entry type: {entry_type}',
                'status': 400
            }), 400
        
        # Validate metadata
        is_valid, error_msg = validator.validate_entry(entry_type, metadata)
        if not is_valid:
            return jsonify({
                'error': f'Validation failed: {error_msg}',
                'status': 400
            }), 400
        
        # Create entry
        entry = Entry(
            type=entry_type,
            metadata=metadata,
            source=data.get('source'),
            agent=data.get('agent', ''),
            tags=data.get('tags', [])
        )
        
        entry_id = entry.save()
        
        # Send notification
        try:
            send_notification(entry_type, metadata, data.get('source'))
        except Exception as e:
            # Notification failure does not affect entry creation
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
    """Get single entry"""
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
    """Update entry"""
    try:
        data = request.json
        entry = Entry.find_by_id(entry_id)
        
        if not entry:
            return jsonify({
                'error': 'Entry not found',
                'status': 404
            }), 404
        
        # If updating metadata, validation required
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
        
        # Update entry
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
    """Delete entry"""
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
    """Batch delete entries"""
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
