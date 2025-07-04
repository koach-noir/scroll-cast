"""
Plugin Registry
プラグイン登録管理システム
"""

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from pathlib import Path
from enum import Enum

from ...monitoring import get_monitor, MetricType


class PluginStatus(Enum):
    """プラグインステータス"""
    UNKNOWN = "unknown"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


class PluginLayer(Enum):
    """プラグイン対象層"""
    BOXING = "boxing"
    COLORING = "coloring"
    PACKING = "packing"
    RENDERING = "rendering"
    ORCHESTRATOR = "orchestrator"
    CUSTOM = "custom"


@dataclass
class PluginDependency:
    """プラグイン依存関係"""
    name: str
    version_requirement: str
    optional: bool = False
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PluginCompatibility:
    """プラグイン互換性情報"""
    subtitle_generator_version: str = ">=1.0.0"
    python_version: str = ">=3.8.0"
    platform: Optional[str] = None  # windows, linux, darwin
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PluginMetadata:
    """プラグインメタデータ"""
    name: str
    version: str
    description: str = ""
    author: str = ""
    license: str = "MIT"
    homepage: str = ""
    layer: PluginLayer = PluginLayer.COLORING
    
    # 技術情報
    entry_point: str = "get_plugin"
    compatibility: PluginCompatibility = field(default_factory=PluginCompatibility)
    dependencies: List[PluginDependency] = field(default_factory=list)
    
    # プラグイン固有設定
    configuration_schema: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['layer'] = self.layer.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        """辞書からメタデータを復元"""
        # 列挙型の復元
        if 'layer' in data:
            data['layer'] = PluginLayer(data['layer'])
        
        # 依存関係の復元
        if 'dependencies' in data:
            data['dependencies'] = [
                PluginDependency(**dep) if isinstance(dep, dict) else dep
                for dep in data['dependencies']
            ]
        
        # 互換性情報の復元
        if 'compatibility' in data and isinstance(data['compatibility'], dict):
            data['compatibility'] = PluginCompatibility(**data['compatibility'])
        
        return cls(**data)


@dataclass
class PluginInfo:
    """プラグイン情報"""
    metadata: PluginMetadata
    path: Path
    status: PluginStatus = PluginStatus.UNKNOWN
    
    # 実行時情報
    load_time: Optional[datetime] = None
    last_access: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None
    
    # パフォーマンス情報
    load_duration: float = 0.0
    execution_count: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        data = {
            'metadata': self.metadata.to_dict(),
            'path': str(self.path),
            'status': self.status.value,
            'load_time': self.load_time.isoformat() if self.load_time else None,
            'last_access': self.last_access.isoformat() if self.last_access else None,
            'error_count': self.error_count,
            'last_error': self.last_error,
            'load_duration': self.load_duration,
            'execution_count': self.execution_count,
            'total_execution_time': self.total_execution_time,
            'average_execution_time': self.average_execution_time
        }
        return data
    
    def update_execution_stats(self, execution_time: float):
        """実行統計を更新"""
        self.execution_count += 1
        self.total_execution_time += execution_time
        self.average_execution_time = self.total_execution_time / self.execution_count
        self.last_access = datetime.now()
    
    def record_error(self, error_message: str):
        """エラーを記録"""
        self.error_count += 1
        self.last_error = error_message
        self.status = PluginStatus.ERROR


class PluginRegistry:
    """プラグイン登録管理"""
    
    def __init__(self, registry_file: Optional[Path] = None):
        self.registry_file = registry_file or Path("plugins_registry.json")
        self.plugins: Dict[str, PluginInfo] = {}
        self.monitor = get_monitor()
        
        # レジストリファイルが存在する場合は読み込み
        if self.registry_file.exists():
            self.load_registry()
    
    def register_plugin(self, plugin_info: PluginInfo) -> bool:
        """プラグインを登録"""
        try:
            plugin_name = plugin_info.metadata.name
            
            # 既存プラグインとの競合チェック
            if plugin_name in self.plugins:
                existing = self.plugins[plugin_name]
                if existing.status == PluginStatus.ACTIVE:
                    print(f"⚠️ Plugin '{plugin_name}' is already active")
                    return False
            
            # 登録
            self.plugins[plugin_name] = plugin_info
            
            # 監視メトリクス記録
            self.monitor.record_metric(
                'plugin_registered', 1.0, MetricType.BUSINESS,
                {
                    'plugin_name': plugin_name,
                    'layer': plugin_info.metadata.layer.value,
                    'version': plugin_info.metadata.version
                }
            )
            
            print(f"✅ Plugin '{plugin_name}' registered successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to register plugin: {e}")
            return False
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """プラグインを登録解除"""
        if plugin_name not in self.plugins:
            print(f"⚠️ Plugin '{plugin_name}' not found")
            return False
        
        plugin_info = self.plugins.pop(plugin_name)
        
        # 監視メトリクス記録
        self.monitor.record_metric(
            'plugin_unregistered', 1.0, MetricType.BUSINESS,
            {'plugin_name': plugin_name}
        )
        
        print(f"✅ Plugin '{plugin_name}' unregistered")
        return True
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInfo]:
        """プラグイン情報を取得"""
        return self.plugins.get(plugin_name)
    
    def list_plugins(self, layer: Optional[PluginLayer] = None, 
                    status: Optional[PluginStatus] = None) -> List[PluginInfo]:
        """プラグイン一覧を取得"""
        plugins = list(self.plugins.values())
        
        if layer:
            plugins = [p for p in plugins if p.metadata.layer == layer]
        
        if status:
            plugins = [p for p in plugins if p.status == status]
        
        return plugins
    
    def get_active_plugins(self) -> List[PluginInfo]:
        """アクティブなプラグイン一覧を取得"""
        return self.list_plugins(status=PluginStatus.ACTIVE)
    
    def get_plugins_by_layer(self, layer: PluginLayer) -> List[PluginInfo]:
        """層別プラグイン一覧を取得"""
        return self.list_plugins(layer=layer)
    
    def update_plugin_status(self, plugin_name: str, status: PluginStatus):
        """プラグインステータスを更新"""
        if plugin_name in self.plugins:
            old_status = self.plugins[plugin_name].status
            self.plugins[plugin_name].status = status
            
            # ステータス変更をメトリクスに記録
            self.monitor.record_metric(
                'plugin_status_changed', 1.0, MetricType.BUSINESS,
                {
                    'plugin_name': plugin_name,
                    'old_status': old_status.value,
                    'new_status': status.value
                }
            )
    
    def record_plugin_execution(self, plugin_name: str, execution_time: float):
        """プラグイン実行を記録"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].update_execution_stats(execution_time)
            
            # パフォーマンスメトリクス記録
            self.monitor.record_metric(
                'plugin_execution_time', execution_time * 1000, MetricType.PERFORMANCE,
                {'plugin_name': plugin_name}
            )
    
    def record_plugin_error(self, plugin_name: str, error_message: str):
        """プラグインエラーを記録"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].record_error(error_message)
            
            # エラーメトリクス記録
            self.monitor.record_metric(
                'plugin_error', 1.0, MetricType.SYSTEM,
                {'plugin_name': plugin_name, 'error': error_message}
            )
    
    def get_plugin_statistics(self) -> Dict[str, Any]:
        """プラグイン統計を取得"""
        total_plugins = len(self.plugins)
        active_plugins = len(self.get_active_plugins())
        error_plugins = len(self.list_plugins(status=PluginStatus.ERROR))
        
        # 層別統計
        layer_stats = {}
        for layer in PluginLayer:
            layer_plugins = self.get_plugins_by_layer(layer)
            layer_stats[layer.value] = {
                'total': len(layer_plugins),
                'active': len([p for p in layer_plugins if p.status == PluginStatus.ACTIVE])
            }
        
        # パフォーマンス統計
        total_executions = sum(p.execution_count for p in self.plugins.values())
        total_errors = sum(p.error_count for p in self.plugins.values())
        
        return {
            'total_plugins': total_plugins,
            'active_plugins': active_plugins,
            'error_plugins': error_plugins,
            'layer_statistics': layer_stats,
            'total_executions': total_executions,
            'total_errors': total_errors,
            'error_rate': total_errors / max(total_executions, 1),
            'registry_file': str(self.registry_file)
        }
    
    def save_registry(self):
        """レジストリをファイルに保存"""
        try:
            registry_data = {
                'plugins': {name: info.to_dict() for name, info in self.plugins.items()},
                'saved_at': datetime.now().isoformat(),
                'version': '1.0.0'
            }
            
            self.registry_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Plugin registry saved to {self.registry_file}")
            
        except Exception as e:
            print(f"❌ Failed to save plugin registry: {e}")
    
    def load_registry(self):
        """レジストリをファイルから読み込み"""
        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                registry_data = json.load(f)
            
            plugins_data = registry_data.get('plugins', {})
            
            for plugin_name, plugin_data in plugins_data.items():
                # メタデータ復元
                metadata = PluginMetadata.from_dict(plugin_data['metadata'])
                
                # プラグイン情報復元
                plugin_info = PluginInfo(
                    metadata=metadata,
                    path=Path(plugin_data['path']),
                    status=PluginStatus(plugin_data['status']),
                    error_count=plugin_data.get('error_count', 0),
                    last_error=plugin_data.get('last_error'),
                    load_duration=plugin_data.get('load_duration', 0.0),
                    execution_count=plugin_data.get('execution_count', 0),
                    total_execution_time=plugin_data.get('total_execution_time', 0.0),
                    average_execution_time=plugin_data.get('average_execution_time', 0.0)
                )
                
                # 日時情報復元
                if plugin_data.get('load_time'):
                    plugin_info.load_time = datetime.fromisoformat(plugin_data['load_time'])
                if plugin_data.get('last_access'):
                    plugin_info.last_access = datetime.fromisoformat(plugin_data['last_access'])
                
                self.plugins[plugin_name] = plugin_info
            
            print(f"✅ Plugin registry loaded from {self.registry_file}")
            print(f"   Loaded {len(self.plugins)} plugins")
            
        except Exception as e:
            print(f"❌ Failed to load plugin registry: {e}")
    
    def cleanup_invalid_plugins(self) -> int:
        """無効なプラグインをクリーンアップ"""
        invalid_plugins = []
        
        for plugin_name, plugin_info in self.plugins.items():
            # ファイルの存在チェック
            if not plugin_info.path.exists():
                invalid_plugins.append(plugin_name)
                continue
            
            # エラー状態のプラグインのチェック
            if (plugin_info.status == PluginStatus.ERROR and 
                plugin_info.error_count > 5):  # 5回以上エラー
                invalid_plugins.append(plugin_name)
        
        # 無効なプラグインを削除
        for plugin_name in invalid_plugins:
            self.unregister_plugin(plugin_name)
        
        if invalid_plugins:
            print(f"🧹 Cleaned up {len(invalid_plugins)} invalid plugins")
        
        return len(invalid_plugins)
    
    def print_summary(self):
        """レジストリサマリーを表示"""
        stats = self.get_plugin_statistics()
        
        print("\n" + "="*50)
        print("📋 PLUGIN REGISTRY SUMMARY")
        print("="*50)
        
        print(f"Total Plugins: {stats['total_plugins']}")
        print(f"Active Plugins: {stats['active_plugins']}")
        print(f"Error Plugins: {stats['error_plugins']}")
        print(f"Total Executions: {stats['total_executions']}")
        print(f"Error Rate: {stats['error_rate']:.1%}")
        
        print(f"\n📊 Layer Statistics:")
        for layer, layer_stats in stats['layer_statistics'].items():
            print(f"  {layer}: {layer_stats['active']}/{layer_stats['total']} active")
        
        if self.plugins:
            print(f"\n🔌 Plugin List:")
            for plugin_name, plugin_info in self.plugins.items():
                status_icon = {
                    PluginStatus.ACTIVE: "🟢",
                    PluginStatus.LOADED: "🟡", 
                    PluginStatus.ERROR: "🔴",
                    PluginStatus.DISABLED: "⚫"
                }.get(plugin_info.status, "⚪")
                
                print(f"  {status_icon} {plugin_name} ({plugin_info.metadata.version}) "
                      f"- {plugin_info.metadata.layer.value}")
        
        print("="*50)


# グローバルレジストリインスタンス
_global_registry: Optional[PluginRegistry] = None


def get_plugin_registry() -> PluginRegistry:
    """グローバルプラグインレジストリを取得"""
    global _global_registry
    if _global_registry is None:
        _global_registry = PluginRegistry()
    return _global_registry