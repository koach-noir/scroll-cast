"""
Configuration Loader for YAML/JSON Template Settings
YAML/JSON設定ファイルからテンプレート設定を読み込み
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from ..coloring.parameters import get_parameter_class, create_parameters


class PresetConfig(BaseModel):
    """プリセット設定"""
    name: str = Field(..., description="プリセット名")
    description: str = Field(default="", description="プリセット説明")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="パラメータ値")


class TemplateConfig(BaseModel):
    """テンプレート設定"""
    template_name: str = Field(..., description="テンプレート名")
    version: str = Field(default="1.0.0", description="設定バージョン")
    description: str = Field(default="", description="テンプレート説明")
    author: str = Field(default="", description="作成者")
    
    # パラメータ設定
    default_parameters: Dict[str, Any] = Field(default_factory=dict, description="デフォルトパラメータ")
    parameter_constraints: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="パラメータ制約")
    
    # プリセット
    presets: List[PresetConfig] = Field(default_factory=list, description="プリセット一覧")
    
    # メタデータ
    tags: List[str] = Field(default_factory=list, description="タグ")
    category: str = Field(default="general", description="カテゴリ")
    
    @field_validator('template_name')
    @classmethod
    def validate_template_name(cls, v):
        """テンプレート名の検証"""
        if not v or not v.strip():
            raise ValueError("Template name cannot be empty")
        return v.strip()
    
    def get_preset_parameters(self, preset_name: str) -> Optional[Dict[str, Any]]:
        """プリセット名からパラメータを取得"""
        for preset in self.presets:
            if preset.name == preset_name:
                # デフォルトパラメータとプリセットパラメータをマージ
                merged_params = self.default_parameters.copy()
                merged_params.update(preset.parameters)
                return merged_params
        return None
    
    def get_all_preset_names(self) -> List[str]:
        """すべてのプリセット名を取得"""
        return [preset.name for preset in self.presets]


class ConfigLoader:
    """設定ファイルローダー"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Args:
            config_dir: 設定ディレクトリパス（Noneの場合はプロジェクトルート/config）
        """
        if config_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            config_dir = project_root / "config"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # 設定ファイルのキャッシュ
        self._config_cache: Dict[str, TemplateConfig] = {}
        
    def load_template_config(self, template_name: str) -> Optional[TemplateConfig]:
        """テンプレート設定を読み込み"""
        # キャッシュから確認
        if template_name in self._config_cache:
            return self._config_cache[template_name]
        
        # 設定ファイルを検索
        config_file = self._find_config_file(template_name)
        if not config_file:
            return None
        
        try:
            config_data = self._load_config_file(config_file)
            template_config = TemplateConfig(**config_data)
            
            # キャッシュに保存
            self._config_cache[template_name] = template_config
            return template_config
            
        except Exception as e:
            print(f"Warning: Failed to load config for {template_name}: {e}")
            return None
    
    def _find_config_file(self, template_name: str) -> Optional[Path]:
        """設定ファイルを検索"""
        # 優先順位: YAML > JSON
        for ext in ['.yaml', '.yml', '.json']:
            config_file = self.config_dir / f"{template_name}{ext}"
            if config_file.exists():
                return config_file
        return None
    
    def _load_config_file(self, config_file: Path) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        with open(config_file, 'r', encoding='utf-8') as f:
            if config_file.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            else:
                return json.load(f)
    
    def create_parameters_from_config(self, template_name: str, preset_name: Optional[str] = None, **override_params) -> Optional[Any]:
        """設定ファイルからパラメータオブジェクトを作成"""
        config = self.load_template_config(template_name)
        if not config:
            return None
        
        # パラメータの優先順位: override_params > preset > default
        parameters = config.default_parameters.copy()
        
        if preset_name:
            preset_params = config.get_preset_parameters(preset_name)
            if preset_params:
                parameters.update(preset_params)
        
        parameters.update(override_params)
        
        # Pydanticパラメータオブジェクトを作成
        return create_parameters(template_name, **parameters)
    
    def save_template_config(self, template_config: TemplateConfig, format: str = "yaml") -> bool:
        """テンプレート設定を保存"""
        try:
            if format.lower() == "yaml":
                config_file = self.config_dir / f"{template_config.template_name}.yaml"
                with open(config_file, 'w', encoding='utf-8') as f:
                    yaml.dump(template_config.model_dump(), f, default_flow_style=False, allow_unicode=True)
            else:
                config_file = self.config_dir / f"{template_config.template_name}.json"
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(template_config.model_dump(), f, indent=2, ensure_ascii=False)
            
            # キャッシュを更新
            self._config_cache[template_config.template_name] = template_config
            return True
            
        except Exception as e:
            print(f"Error: Failed to save config for {template_config.template_name}: {e}")
            return False
    
    def list_available_templates(self) -> List[str]:
        """利用可能なテンプレート一覧を取得"""
        templates = []
        for config_file in self.config_dir.glob("*.yaml"):
            templates.append(config_file.stem)
        for config_file in self.config_dir.glob("*.yml"):
            if config_file.stem not in templates:
                templates.append(config_file.stem)
        for config_file in self.config_dir.glob("*.json"):
            if config_file.stem not in templates:
                templates.append(config_file.stem)
        return sorted(templates)
    
    def clear_cache(self):
        """キャッシュをクリア"""
        self._config_cache.clear()