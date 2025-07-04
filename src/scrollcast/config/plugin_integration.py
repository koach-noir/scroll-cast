"""
Plugin Parameter Integration
プラグインシステムとパラメータシステムの統合
"""

from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import json
import yaml
from pydantic import BaseModel, Field

from .config_loader import ConfigLoader, TemplateConfig, PresetConfig
from .schema_validator import SchemaValidator, ValidationResult
from ..plugins.core.plugin_manager import get_plugin_manager
from ..plugins.core.registry import PluginStatus, PluginLayer
from ..coloring.parameters import create_parameters, get_parameter_class


class PluginParameterConfig(BaseModel):
    """プラグイン用パラメータ設定"""
    plugin_name: str = Field(..., description="プラグイン名")
    template_name: str = Field(..., description="テンプレート名")
    version: str = Field(default="1.0.0", description="設定バージョン")
    
    # パラメータ設定
    external_config_path: Optional[str] = Field(default=None, description="外部設定ファイルパス")
    parameter_mappings: Dict[str, str] = Field(default_factory=dict, description="パラメータマッピング")
    default_overrides: Dict[str, Any] = Field(default_factory=dict, description="デフォルト値オーバーライド")
    
    # 動的設定
    enable_hot_reload: bool = Field(default=False, description="ホットリロード有効化")
    validation_level: str = Field(default="strict", description="検証レベル")


class PluginParameterIntegrator:
    """プラグインパラメータ統合クラス"""
    
    def __init__(self, 
                 config_loader: Optional[ConfigLoader] = None,
                 validator: Optional[SchemaValidator] = None):
        """
        Args:
            config_loader: 設定ローダー
            validator: スキーマ検証器
        """
        self.config_loader = config_loader or ConfigLoader()
        self.validator = validator or SchemaValidator()
        self.plugin_manager = get_plugin_manager()
        
        # プラグイン用設定キャッシュ
        self._plugin_configs: Dict[str, PluginParameterConfig] = {}
        
        # 外部設定監視
        self._external_config_cache: Dict[str, Dict[str, Any]] = {}
        self._external_config_timestamps: Dict[str, float] = {}
    
    def register_plugin_config(self, plugin_name: str, config: PluginParameterConfig) -> bool:
        """プラグイン設定を登録"""
        try:
            self._plugin_configs[plugin_name] = config
            print(f"✅ Plugin config registered for '{plugin_name}'")
            return True
        except Exception as e:
            print(f"❌ Failed to register plugin config for '{plugin_name}': {e}")
            return False
    
    def create_plugin_parameters(self, 
                                plugin_name: str, 
                                preset_name: Optional[str] = None,
                                external_overrides: Optional[Dict[str, Any]] = None,
                                **local_overrides) -> Optional[Any]:
        """プラグイン用パラメータを作成"""
        try:
            # プラグイン設定を取得
            plugin_config = self._plugin_configs.get(plugin_name)
            if not plugin_config:
                # プラグインマネージャーから基本情報を取得
                plugin_info = self.plugin_manager.registry.get_plugin(plugin_name)
                if not plugin_info:
                    print(f"⚠️ Plugin '{plugin_name}' not found")
                    return None
                
                # デフォルト設定を作成
                plugin_config = PluginParameterConfig(
                    plugin_name=plugin_name,
                    template_name=plugin_name  # デフォルトではプラグイン名と同じ
                )
                self._plugin_configs[plugin_name] = plugin_config
            
            # パラメータの優先順位を設定
            # 1. ベースパラメータ（テンプレート設定から）
            template_name = plugin_config.template_name
            parameters = {}
            
            # 設定ファイルからベース値を取得
            config = self.config_loader.load_template_config(template_name)
            if config:
                parameters.update(config.default_parameters)
                
                # プリセット適用
                if preset_name:
                    preset_params = config.get_preset_parameters(preset_name)
                    if preset_params:
                        parameters.update(preset_params)
            
            # 2. プラグイン設定のデフォルトオーバーライド
            parameters.update(plugin_config.default_overrides)
            
            # 3. 外部設定ファイルから読み込み
            if plugin_config.external_config_path:
                external_params = self._load_external_config(plugin_config.external_config_path)
                if external_params:
                    # パラメータマッピングを適用
                    mapped_params = self._apply_parameter_mapping(
                        external_params, 
                        plugin_config.parameter_mappings
                    )
                    parameters.update(mapped_params)
            
            # 4. 外部オーバーライド
            if external_overrides:
                parameters.update(external_overrides)
            
            # 5. ローカルオーバーライド（最優先）
            parameters.update(local_overrides)
            
            # パラメータ検証
            if plugin_config.validation_level == "strict":
                validation_result = self.validator.validate_template_parameters(template_name, parameters)
                if not validation_result.is_valid:
                    print(f"❌ Parameter validation failed for '{plugin_name}':")
                    for error in validation_result.errors:
                        print(f"  - {error}")
                    return None
                
                if validation_result.warnings:
                    print(f"⚠️ Parameter warnings for '{plugin_name}':")
                    for warning in validation_result.warnings:
                        print(f"  - {warning}")
                
                parameters = validation_result.validated_data
            
            # Pydanticパラメータオブジェクトを作成
            return create_parameters(template_name, **parameters)
            
        except Exception as e:
            print(f"❌ Failed to create parameters for plugin '{plugin_name}': {e}")
            return None
    
    def _load_external_config(self, config_path: str) -> Optional[Dict[str, Any]]:
        """外部設定ファイルを読み込み"""
        try:
            file_path = Path(config_path)
            
            # ファイル存在チェック
            if not file_path.exists():
                print(f"⚠️ External config file not found: {config_path}")
                return None
            
            # ホットリロード対応（タイムスタンプチェック）
            current_timestamp = file_path.stat().st_mtime
            cached_timestamp = self._external_config_timestamps.get(config_path)
            
            if cached_timestamp == current_timestamp and config_path in self._external_config_cache:
                return self._external_config_cache[config_path]
            
            # ファイル読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                elif file_path.suffix == '.json':
                    config_data = json.load(f)
                else:
                    print(f"⚠️ Unsupported config file format: {file_path.suffix}")
                    return None
            
            # キャッシュ更新
            self._external_config_cache[config_path] = config_data
            self._external_config_timestamps[config_path] = current_timestamp
            
            return config_data
            
        except Exception as e:
            print(f"❌ Failed to load external config '{config_path}': {e}")
            return None
    
    def _apply_parameter_mapping(self, 
                                external_params: Dict[str, Any], 
                                mappings: Dict[str, str]) -> Dict[str, Any]:
        """パラメータマッピングを適用"""
        mapped_params = {}
        
        for internal_name, external_name in mappings.items():
            if external_name in external_params:
                mapped_params[internal_name] = external_params[external_name]
        
        # マッピングされていないパラメータもそのまま追加
        for key, value in external_params.items():
            if key not in mappings.values() and key not in mapped_params:
                mapped_params[key] = value
        
        return mapped_params
    
    def setup_plugin_from_config_file(self, plugin_name: str, config_file_path: str) -> bool:
        """設定ファイルからプラグインを設定"""
        try:
            config_path = Path(config_file_path)
            
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)
            
            # プラグイン設定を作成
            plugin_config = PluginParameterConfig(**config_data)
            
            return self.register_plugin_config(plugin_name, plugin_config)
            
        except Exception as e:
            print(f"❌ Failed to setup plugin from config file '{config_file_path}': {e}")
            return False
    
    def get_plugin_parameter_schema(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """プラグインのパラメータスキーマを取得"""
        plugin_config = self._plugin_configs.get(plugin_name)
        if not plugin_config:
            return None
        
        return self.validator.get_parameter_schema(plugin_config.template_name)
    
    def validate_plugin_parameters(self, 
                                  plugin_name: str, 
                                  parameters: Dict[str, Any]) -> ValidationResult:
        """プラグインパラメータを検証"""
        plugin_config = self._plugin_configs.get(plugin_name)
        if not plugin_config:
            return ValidationResult(
                is_valid=False, 
                errors=[f"Plugin config not found for '{plugin_name}'"]
            )
        
        return self.validator.validate_template_parameters(
            plugin_config.template_name, 
            parameters
        )
    
    def list_configured_plugins(self) -> List[str]:
        """設定済みプラグイン一覧を取得"""
        return list(self._plugin_configs.keys())
    
    def export_plugin_config(self, plugin_name: str, export_path: str) -> bool:
        """プラグイン設定をエクスポート"""
        try:
            plugin_config = self._plugin_configs.get(plugin_name)
            if not plugin_config:
                print(f"⚠️ Plugin config not found for '{plugin_name}'")
                return False
            
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                if export_file.suffix in ['.yaml', '.yml']:
                    yaml.dump(plugin_config.model_dump(), f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(plugin_config.model_dump(), f, indent=2, ensure_ascii=False)
            
            print(f"✅ Plugin config exported to '{export_path}'")
            return True
            
        except Exception as e:
            print(f"❌ Failed to export plugin config: {e}")
            return False
    
    def sync_with_plugin_manager(self) -> bool:
        """プラグインマネージャーと同期"""
        try:
            active_plugins = self.plugin_manager.list_active_plugins()
            available_templates = self.plugin_manager.list_available_templates()
            
            print(f"🔄 Syncing with plugin manager:")
            print(f"  Active plugins: {len(active_plugins)}")
            print(f"  Available templates: {len(available_templates)}")
            
            # アクティブプラグインの設定を確認
            for plugin_name in active_plugins:
                if plugin_name not in self._plugin_configs:
                    # デフォルト設定を作成
                    plugin_info = self.plugin_manager.registry.get_plugin(plugin_name)
                    if plugin_info and plugin_info.metadata.layer == PluginLayer.COLORING:
                        default_config = PluginParameterConfig(
                            plugin_name=plugin_name,
                            template_name=plugin_name
                        )
                        self._plugin_configs[plugin_name] = default_config
                        print(f"  ✅ Created default config for '{plugin_name}'")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to sync with plugin manager: {e}")
            return False
    
    def clear_cache(self):
        """キャッシュをクリア"""
        self._external_config_cache.clear()
        self._external_config_timestamps.clear()
        self.config_loader.clear_cache()
        print("🧹 Parameter integration cache cleared")
    
    def get_integration_status(self) -> Dict[str, Any]:
        """統合システムの状態を取得"""
        plugin_manager_health = self.plugin_manager.get_plugin_health_status()
        
        return {
            'configured_plugins': len(self._plugin_configs),
            'active_plugins': len(self.plugin_manager.list_active_plugins()),
            'external_configs': len(self._external_config_cache),
            'template_configs': len(self.config_loader.list_available_templates()),
            'plugin_manager_health': plugin_manager_health['health_score'],
            'integration_health': self._calculate_integration_health()
        }
    
    def _calculate_integration_health(self) -> float:
        """統合システムのヘルス値を計算"""
        try:
            # 設定済みプラグインとアクティブプラグインの一致度
            configured = set(self._plugin_configs.keys())
            active = set(self.plugin_manager.list_active_plugins())
            
            if not active:
                return 100.0  # プラグインがない場合は問題なし
            
            match_rate = len(configured & active) / len(active)
            
            # 外部設定ファイルの読み込み成功率
            external_success_rate = 1.0
            if self._external_config_cache:
                failed_configs = sum(1 for v in self._external_config_cache.values() if v is None)
                external_success_rate = 1.0 - (failed_configs / len(self._external_config_cache))
            
            # 総合ヘルス計算
            health = (match_rate * 0.7 + external_success_rate * 0.3) * 100
            return round(health, 1)
            
        except Exception:
            return 0.0