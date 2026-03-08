import json
import os
from typing import Dict, Optional, List


class TypeManager:
    """管理Entry类型配置"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__),
                'entry_types.json'
            )
        self.config_path = config_path
        self._types = self._load_types()
    
    def _load_types(self) -> Dict:
        """加载类型配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._get_default_types()
    
    def _get_default_types(self) -> Dict:
        """获取默认类型配置"""
        return {
            "message": {
                "name": "留言",
                "description": "用户留言",
                "schema": {
                    "type": "object",
                    "required": ["name", "email", "content"],
                    "properties": {
                        "name": {"type": "string", "minLength": 1, "maxLength": 50},
                        "email": {"type": "string", "format": "email"},
                        "website": {"type": "string"},
                        "content": {"type": "string", "minLength": 1, "maxLength": 1000}
                    }
                },
                "notification": {
                    "enabled": True,
                    "template": "wechat_message"
                }
            }
        }
    
    def get_type(self, type_name: str) -> Optional[Dict]:
        """获取特定类型的配置"""
        return self._types.get(type_name)
    
    def get_schema(self, type_name: str) -> Optional[Dict]:
        """获取特定类型的schema"""
        type_config = self.get_type(type_name)
        return type_config.get('schema') if type_config else None
    
    def get_all_types(self) -> Dict:
        """获取所有类型配置"""
        return self._types
    
    def type_exists(self, type_name: str) -> bool:
        """检查类型是否存在"""
        return type_name in self._types
    
    def add_type(self, type_name: str, config: Dict) -> bool:
        """添加新类型"""
        if type_name in self._types:
            return False
        
        self._types[type_name] = config
        self._save_types()
        return True
    
    def update_type(self, type_name: str, config: Dict) -> bool:
        """更新类型配置"""
        if type_name not in self._types:
            return False
        
        self._types[type_name] = config
        self._save_types()
        return True
    
    def _save_types(self):
        """保存类型配置到文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._types, f, ensure_ascii=False, indent=2)
    
    def get_notification_config(self, type_name: str) -> Optional[Dict]:
        """获取类型的通知配置"""
        type_config = self.get_type(type_name)
        return type_config.get('notification') if type_config else None


# 全局实例
type_manager = TypeManager()

# Made with Bob
