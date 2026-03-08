from app import mongo
from datetime import datetime
from bson import ObjectId
from typing import Dict, List, Optional


class Entry:
    """Universal Entry model supporting multiple data types"""
    
    def __init__(
        self,
        type: str,
        metadata: Dict,
        source: Optional[str] = None,
        status: Optional[Dict] = None,
        timestamps: Optional[Dict] = None,
        agent: Optional[str] = None,
        tags: Optional[List[str]] = None,
        id: Optional[str] = None
    ):
        self.id = ObjectId(id) if id else None
        self.type = type
        self.source = source
        self.metadata = metadata
        self.status = status or {
            'is_show': False,
            'is_delete': False,
            'is_read': False
        }
        self.timestamps = timestamps or {}
        self.agent = agent or ''
        self.tags = tags or []
    
    def save(self) -> str:
        """Save Entry to database"""
        current_time = datetime.now()
        
        document = {
            'type': self.type,
            'source': self.source,
            'metadata': self.metadata,
            'status': self.status,
            'timestamps': {
                'create_time': self.timestamps.get('create_time', current_time),
                'update_time': current_time,
                'admin_time': self.timestamps.get('admin_time', current_time),
                'delete_time': self.timestamps.get('delete_time')
            },
            'agent': self.agent,
            'tags': self.tags
        }
        
        if self.id:
            # Update existing entry
            mongo.db.entries.update_one(
                {'_id': self.id},
                {'$set': document}
            )
            return str(self.id)
        else:
            # Create new entry
            result = mongo.db.entries.insert_one(document)
            return str(result.inserted_id)
    
    def delete(self):
        """Delete Entry"""
        if self.id:
            mongo.db.entries.delete_one({'_id': self.id})
    
    @staticmethod
    def find_by_id(entry_id: str) -> Optional[Dict]:
        """Find Entry by ID"""
        try:
            return mongo.db.entries.find_one({'_id': ObjectId(entry_id)})
        except Exception:
            return None
    
    @staticmethod
    def find_all(filters: Optional[Dict] = None, page: int = 1, limit: int = 20) -> tuple:
        """Find all Entries matching criteria"""
        filters = filters or {}
        skip = (page - 1) * limit
        
        cursor = mongo.db.entries.find(filters).skip(skip).limit(limit).sort('timestamps.create_time', -1)
        total = mongo.db.entries.count_documents(filters)
        
        return list(cursor), total
    
    @staticmethod
    def find_visible(type: Optional[str] = None, source: Optional[str] = None) -> List[Dict]:
        """Find visible Entries"""
        filters = {'status.is_show': True, 'status.is_delete': False}
        
        if type:
            filters['type'] = type
        if source:
            filters['source'] = source
        
        return list(mongo.db.entries.find(filters).sort('timestamps.create_time', -1))
    
    @staticmethod
    def update_status(entry_id: str, status_updates: Dict) -> bool:
        """Update Entry status"""
        update_fields = {}
        
        for key, value in status_updates.items():
            if key in ['is_show', 'is_delete', 'is_read']:
                update_fields[f'status.{key}'] = bool(value)
        
        if not update_fields:
            return False
        
        update_fields['timestamps.admin_time'] = datetime.now()
        
        result = mongo.db.entries.update_one(
            {'_id': ObjectId(entry_id)},
            {'$set': update_fields}
        )
        
        return result.matched_count > 0
    
    @staticmethod
    def delete_many(entry_ids: List[str]) -> int:
        """Batch delete Entries"""
        object_ids = [ObjectId(id) for id in entry_ids]
        result = mongo.db.entries.delete_many({'_id': {'$in': object_ids}})
        return result.deleted_count
    
    @staticmethod
    def get_stats(filters: Optional[Dict] = None) -> Dict:
        """Get statistics"""
        filters = filters or {}
        
        pipeline = [
            {'$match': filters},
            {'$group': {
                '_id': '$type',
                'count': {'$sum': 1},
                'visible': {
                    '$sum': {
                        '$cond': [
                            {'$and': [
                                {'$eq': ['$status.is_show', True]},
                                {'$eq': ['$status.is_delete', False]}
                            ]},
                            1,
                            0
                        ]
                    }
                }
            }}
        ]
        
        results = list(mongo.db.entries.aggregate(pipeline))
        
        stats = {
            'total': sum(r['count'] for r in results),
            'by_type': {r['_id']: r for r in results}
        }
        
        return stats

# Made with Bob
