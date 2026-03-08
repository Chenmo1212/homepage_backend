from jsonschema import validate, ValidationError, FormatChecker
from typing import Dict, Tuple
from app.config.type_manager import type_manager


class SchemaValidator:
    """JSON Schema验证器"""
    
    @staticmethod
    def validate_entry(type_name: str, metadata: Dict) -> Tuple[bool, str]:
        """
        验证entry的metadata是否符合类型schema
        
        Returns:
            (is_valid, error_message)
        """
        schema = type_manager.get_schema(type_name)
        
        if not schema:
            return False, f"Unknown entry type: {type_name}"
        
        try:
            validate(
                instance=metadata,
                schema=schema,
                format_checker=FormatChecker()
            )
            return True, ""
        except ValidationError as e:
            return False, str(e.message)
    
    @staticmethod
    def validate_type_config(config: Dict) -> Tuple[bool, str]:
        """验证类型配置是否有效"""
        required_fields = ['name', 'schema']
        
        for field in required_fields:
            if field not in config:
                return False, f"Missing required field: {field}"
        
        # 验证schema本身的结构
        schema = config['schema']
        if not isinstance(schema, dict):
            return False, "Schema must be a dictionary"
        
        if 'type' not in schema:
            return False, "Schema must have a 'type' field"
        
        return True, ""


# 全局实例
validator = SchemaValidator()

# Made with Bob
