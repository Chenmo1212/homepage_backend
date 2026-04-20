from jsonschema import validate, ValidationError, FormatChecker
from typing import Dict, Tuple
from app.modules.homepage.config.type_manager import type_manager


class SchemaValidator:
    """JSON Schema validator"""
    
    @staticmethod
    def validate_entry(type_name: str, metadata: Dict) -> Tuple[bool, str]:
        """
        Validate if entry metadata conforms to type schema
        
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
        """Validate if type configuration is valid"""
        required_fields = ['name', 'schema']
        
        for field in required_fields:
            if field not in config:
                return False, f"Missing required field: {field}"
        
        # Validate schema structure itself
        schema = config['schema']
        if not isinstance(schema, dict):
            return False, "Schema must be a dictionary"
        
        if 'type' not in schema:
            return False, "Schema must have a 'type' field"
        
        return True, ""


# Global instance
validator = SchemaValidator()

# Made with Bob
