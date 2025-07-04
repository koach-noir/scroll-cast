"""
Schema Validator for Template Configuration
テンプレート設定のスキーマ検証
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, ValidationError
from ..coloring.parameters import get_parameter_class, PARAMETER_CLASSES


class ValidationResult(BaseModel):
    """検証結果"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    validated_data: Optional[Dict[str, Any]] = None


class SchemaValidator:
    """スキーマ検証クラス"""
    
    def __init__(self):
        """初期化"""
        self.parameter_classes = PARAMETER_CLASSES
    
    def validate_template_parameters(self, template_name: str, parameters: Dict[str, Any]) -> ValidationResult:
        """テンプレートパラメータの検証"""
        errors = []
        warnings = []
        validated_data = None
        
        # テンプレート名の検証
        if template_name not in self.parameter_classes:
            errors.append(f"Unknown template: {template_name}")
            return ValidationResult(is_valid=False, errors=errors)
        
        # パラメータクラスを取得
        parameter_class = self.parameter_classes[template_name]
        
        try:
            # Pydanticによる検証
            validated_obj = parameter_class(**parameters)
            validated_data = validated_obj.model_dump()
            
            # 追加の検証
            additional_warnings = self._validate_parameter_combinations(template_name, validated_data)
            warnings.extend(additional_warnings)
            
        except ValidationError as e:
            for error in e.errors():
                field_name = " -> ".join(str(x) for x in error['loc'])
                error_msg = f"Field '{field_name}': {error['msg']}"
                errors.append(error_msg)
        except Exception as e:
            errors.append(f"Unexpected validation error: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validated_data=validated_data
        )
    
    def _validate_parameter_combinations(self, template_name: str, parameters: Dict[str, Any]) -> List[str]:
        """パラメータの組み合わせ検証"""
        warnings = []
        
        if template_name == 'typewriter_fade':
            # タイプライター効果の組み合わせ検証
            char_interval = parameters.get('char_interval', 0.15)
            fade_duration = parameters.get('fade_duration', 0.1)
            
            if char_interval < fade_duration * 2:
                warnings.append(
                    f"char_interval ({char_interval}s) is very close to fade_duration ({fade_duration}s). "
                    "Consider increasing char_interval for better visual effect."
                )
        
        elif template_name == 'railway_scroll':
            # 鉄道スクロール効果の組み合わせ検証
            fade_in = parameters.get('fade_in_duration', 0.8)
            fade_out = parameters.get('fade_out_duration', 0.8)
            pause = parameters.get('pause_duration', 2.0)
            
            total_duration = fade_in + fade_out + pause
            if total_duration > 8.0:
                warnings.append(
                    f"Total duration ({total_duration:.1f}s) is quite long. "
                    "Consider reducing fade or pause durations for better pacing."
                )
        
        elif template_name == 'simple_role':
            # シンプルロール効果の組み合わせ検証
            animation_duration = parameters.get('animation_duration', 8.0)
            line_interval = parameters.get('line_interval', 0.2)
            scroll_speed = parameters.get('scroll_speed', 1.0)
            
            if animation_duration < 5.0 and scroll_speed > 1.5:
                warnings.append(
                    f"Short animation ({animation_duration}s) with high scroll speed ({scroll_speed}) "
                    "might be too fast to read comfortably."
                )
        
        return warnings
    
    def validate_preset_parameters(self, template_name: str, preset_data: Dict[str, Any]) -> ValidationResult:
        """プリセットパラメータの検証"""
        # プリセットの基本構造検証
        errors = []
        warnings = []
        
        required_fields = ['name', 'parameters']
        for field in required_fields:
            if field not in preset_data:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return ValidationResult(is_valid=False, errors=errors)
        
        # パラメータの検証
        parameters = preset_data.get('parameters', {})
        param_result = self.validate_template_parameters(template_name, parameters)
        
        if not param_result.is_valid:
            errors.extend([f"Preset parameter error: {error}" for error in param_result.errors])
        
        warnings.extend(param_result.warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validated_data=preset_data if len(errors) == 0 else None
        )
    
    def validate_config_file(self, config_data: Dict[str, Any]) -> ValidationResult:
        """設定ファイル全体の検証"""
        errors = []
        warnings = []
        
        # 基本構造の検証
        if 'template_name' not in config_data:
            errors.append("Missing required field: template_name")
            return ValidationResult(is_valid=False, errors=errors)
        
        template_name = config_data['template_name']
        
        # デフォルトパラメータの検証
        if 'default_parameters' in config_data:
            default_result = self.validate_template_parameters(template_name, config_data['default_parameters'])
            if not default_result.is_valid:
                errors.extend([f"Default parameter error: {error}" for error in default_result.errors])
            warnings.extend(default_result.warnings)
        
        # プリセットの検証
        if 'presets' in config_data:
            for i, preset in enumerate(config_data['presets']):
                preset_result = self.validate_preset_parameters(template_name, preset)
                if not preset_result.is_valid:
                    errors.extend([f"Preset {i+1} error: {error}" for error in preset_result.errors])
                warnings.extend(preset_result.warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validated_data=config_data if len(errors) == 0 else None
        )
    
    def get_parameter_schema(self, template_name: str) -> Optional[Dict[str, Any]]:
        """テンプレートのパラメータスキーマを取得"""
        if template_name not in self.parameter_classes:
            return None
        
        parameter_class = self.parameter_classes[template_name]
        return parameter_class.model_json_schema()
    
    def get_all_parameter_schemas(self) -> Dict[str, Dict[str, Any]]:
        """すべてのテンプレートのパラメータスキーマを取得"""
        schemas = {}
        for template_name, parameter_class in self.parameter_classes.items():
            schemas[template_name] = parameter_class.model_json_schema()
        return schemas
    
    def validate_parameter_value(self, template_name: str, field_name: str, value: Any) -> ValidationResult:
        """特定のパラメータ値の検証"""
        if template_name not in self.parameter_classes:
            return ValidationResult(is_valid=False, errors=[f"Unknown template: {template_name}"])
        
        parameter_class = self.parameter_classes[template_name]
        
        try:
            # 一時的なオブジェクトを作成して検証
            temp_params = {field_name: value}
            temp_obj = parameter_class(**temp_params)
            
            return ValidationResult(
                is_valid=True,
                validated_data={field_name: getattr(temp_obj, field_name)}
            )
        except ValidationError as e:
            errors = []
            for error in e.errors():
                if error['loc'] == (field_name,):
                    errors.append(f"Field '{field_name}': {error['msg']}")
            
            return ValidationResult(is_valid=False, errors=errors)
        except Exception as e:
            return ValidationResult(is_valid=False, errors=[f"Unexpected error: {str(e)}"])