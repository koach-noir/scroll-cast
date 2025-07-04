"""
Plugin Manager
プラグイン管理システム
"""

import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Type, Union
from datetime import datetime

from .registry import PluginRegistry, PluginInfo, PluginStatus, PluginLayer, get_plugin_registry
from .loader import PluginLoader
from .validator import PluginValidator
from ...interfaces import TemplateProtocol
from ...monitoring import get_monitor, MetricType


class PluginManagerError(Exception):
    """プラグインマネージャーエラー"""
    pass


class PluginManager:
    """プラグイン管理システム"""
    
    def __init__(self, 
                 plugins_directory: Optional[Path] = None,
                 registry: Optional[PluginRegistry] = None):
        
        self.plugins_directory = plugins_directory or Path("plugins")
        self.registry = registry or get_plugin_registry()
        self.validator = PluginValidator()
        self.loader = PluginLoader(self.validator)
        self.monitor = get_monitor()
        
        # アクティブなプラグインインスタンス
        self.active_plugins: Dict[str, Any] = {}
        
        # 初期化
        self._initialize()
    
    def _initialize(self):
        """プラグインマネージャーを初期化"""
        try:
            # プラグインディレクトリ作成
            self.plugins_directory.mkdir(parents=True, exist_ok=True)
            
            # レジストリクリーンアップ
            cleaned_count = self.registry.cleanup_invalid_plugins()
            if cleaned_count > 0:
                print(f"🧹 Cleaned up {cleaned_count} invalid plugins")
            
            print(f"🔌 Plugin Manager initialized")
            print(f"   Plugins directory: {self.plugins_directory}")
            print(f"   Registered plugins: {len(self.registry.plugins)}")
            
        except Exception as e:
            print(f"❌ Failed to initialize plugin manager: {e}")
    
    def install_plugin(self, plugin_path: Path, activate: bool = True) -> bool:
        """プラグインをインストール"""
        try:
            start_time = time.time()
            
            print(f"📦 Installing plugin from {plugin_path}")
            
            # 1. プラグインロード
            plugin_info = self.loader.load_plugin_from_path(plugin_path)
            
            # 2. 依存関係チェック
            dep_validation = self.loader.validate_dependencies(plugin_info.metadata)
            if not dep_validation['valid']:
                missing_deps = dep_validation['missing_dependencies']
                raise PluginManagerError(f"Missing dependencies: {', '.join(missing_deps)}")
            
            # 3. レジストリに登録
            if not self.registry.register_plugin(plugin_info):
                raise PluginManagerError("Failed to register plugin")
            
            # 4. アクティベート（オプション）
            if activate:
                self.activate_plugin(plugin_info.metadata.name)
            
            install_time = time.time() - start_time
            
            # メトリクス記録
            self.monitor.record_metric(
                'plugin_installed', 1.0, MetricType.BUSINESS,
                {
                    'plugin_name': plugin_info.metadata.name,
                    'install_time': install_time,
                    'activated': activate
                }
            )
            
            print(f"✅ Plugin '{plugin_info.metadata.name}' installed successfully in {install_time:.3f}s")
            return True
            
        except Exception as e:
            error_msg = f"Failed to install plugin from {plugin_path}: {str(e)}"
            print(f"❌ {error_msg}")
            return False
    
    def uninstall_plugin(self, plugin_name: str) -> bool:
        """プラグインをアンインストール"""
        try:
            # 1. 非アクティブ化
            self.deactivate_plugin(plugin_name)
            
            # 2. レジストリから削除
            if not self.registry.unregister_plugin(plugin_name):
                print(f"⚠️ Plugin '{plugin_name}' not found in registry")
            
            # 3. モジュールアンロード
            self.loader.unload_plugin(plugin_name)
            
            # メトリクス記録
            self.monitor.record_metric(
                'plugin_uninstalled', 1.0, MetricType.BUSINESS,
                {'plugin_name': plugin_name}
            )
            
            print(f"✅ Plugin '{plugin_name}' uninstalled")
            return True
            
        except Exception as e:
            print(f"❌ Failed to uninstall plugin '{plugin_name}': {str(e)}")
            return False
    
    def activate_plugin(self, plugin_name: str) -> bool:
        """プラグインをアクティベート"""
        try:
            plugin_info = self.registry.get_plugin(plugin_name)
            if not plugin_info:
                raise PluginManagerError(f"Plugin '{plugin_name}' not found")
            
            if plugin_info.status == PluginStatus.ACTIVE:
                print(f"⚠️ Plugin '{plugin_name}' is already active")
                return True
            
            # プラグインインスタンス作成
            plugin_instance = self._create_plugin_instance(plugin_info)
            
            # アクティブプラグインに追加
            self.active_plugins[plugin_name] = plugin_instance
            
            # ステータス更新
            self.registry.update_plugin_status(plugin_name, PluginStatus.ACTIVE)
            
            # メトリクス記録
            self.monitor.record_metric(
                'plugin_activated', 1.0, MetricType.BUSINESS,
                {
                    'plugin_name': plugin_name,
                    'layer': plugin_info.metadata.layer.value
                }
            )
            
            print(f"✅ Plugin '{plugin_name}' activated")
            return True
            
        except Exception as e:
            error_msg = f"Failed to activate plugin '{plugin_name}': {str(e)}"
            self.registry.record_plugin_error(plugin_name, error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def deactivate_plugin(self, plugin_name: str) -> bool:
        """プラグインを非アクティブ化"""
        try:
            if plugin_name not in self.active_plugins:
                print(f"⚠️ Plugin '{plugin_name}' is not active")
                return True
            
            # アクティブプラグインから削除
            del self.active_plugins[plugin_name]
            
            # ステータス更新
            self.registry.update_plugin_status(plugin_name, PluginStatus.LOADED)
            
            # メトリクス記録
            self.monitor.record_metric(
                'plugin_deactivated', 1.0, MetricType.BUSINESS,
                {'plugin_name': plugin_name}
            )
            
            print(f"✅ Plugin '{plugin_name}' deactivated")
            return True
            
        except Exception as e:
            print(f"❌ Failed to deactivate plugin '{plugin_name}': {str(e)}")
            return False
    
    def _create_plugin_instance(self, plugin_info: PluginInfo) -> Any:
        """プラグインインスタンスを作成"""
        # モジュールが既にロードされているかチェック
        module_name = plugin_info.metadata.name
        if module_name not in self.loader.loaded_modules:
            # 再ロードが必要
            updated_plugin_info = self.loader.load_plugin_from_path(plugin_info.path)
            self.registry.plugins[plugin_info.metadata.name] = updated_plugin_info
            plugin_info = updated_plugin_info
        
        module = self.loader.loaded_modules[module_name]
        entry_point = plugin_info.metadata.entry_point
        
        if not hasattr(module, entry_point):
            raise PluginManagerError(f"Entry point '{entry_point}' not found")
        
        entry_func = getattr(module, entry_point)
        return entry_func()
    
    def discover_plugins(self, auto_install: bool = False) -> List[Path]:
        """プラグインを発見"""
        print(f"🔍 Discovering plugins in {self.plugins_directory}")
        
        plugin_paths = self.loader.scan_plugins_directory(self.plugins_directory)
        
        if auto_install:
            for plugin_path in plugin_paths:
                # 既に登録されているかチェック
                try:
                    metadata = self.loader.load_metadata(plugin_path)
                    if not self.registry.get_plugin(metadata.name):
                        self.install_plugin(plugin_path, activate=False)
                except Exception as e:
                    print(f"⚠️ Skipped auto-install for {plugin_path}: {str(e)}")
        
        return plugin_paths
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """プラグインをリロード"""
        try:
            plugin_info = self.registry.get_plugin(plugin_name)
            if not plugin_info:
                raise PluginManagerError(f"Plugin '{plugin_name}' not found")
            
            was_active = plugin_info.status == PluginStatus.ACTIVE
            
            # 1. 非アクティブ化
            if was_active:
                self.deactivate_plugin(plugin_name)
            
            # 2. リロード
            new_plugin_info = self.loader.reload_plugin(plugin_info)
            self.registry.plugins[plugin_name] = new_plugin_info
            
            # 3. 再アクティブ化
            if was_active:
                self.activate_plugin(plugin_name)
            
            print(f"🔄 Plugin '{plugin_name}' reloaded")
            return True
            
        except Exception as e:
            print(f"❌ Failed to reload plugin '{plugin_name}': {str(e)}")
            return False
    
    def get_plugin_instance(self, plugin_name: str) -> Optional[Any]:
        """アクティブなプラグインインスタンスを取得"""
        return self.active_plugins.get(plugin_name)
    
    def create_plugin_template(self, template_name: str) -> Optional[TemplateProtocol]:
        """プラグインテンプレートを作成"""
        # coloring層のアクティブプラグインを検索
        coloring_plugins = [
            (name, plugin) for name, plugin in self.active_plugins.items()
            if self.registry.get_plugin(name) and 
            self.registry.get_plugin(name).metadata.layer == PluginLayer.COLORING
        ]
        
        for plugin_name, plugin_instance in coloring_plugins:
            # テンプレート名が一致するかチェック
            if hasattr(plugin_instance, 'template_info'):
                template_info = plugin_instance.template_info
                if hasattr(template_info, 'name') and template_info.name == template_name:
                    # 実行時間を記録
                    start_time = time.time()
                    result = plugin_instance
                    execution_time = time.time() - start_time
                    
                    self.registry.record_plugin_execution(plugin_name, execution_time)
                    return result
            
            # メタデータ名での一致チェック
            plugin_info = self.registry.get_plugin(plugin_name)
            if plugin_info and plugin_info.metadata.name == template_name:
                start_time = time.time()
                result = plugin_instance
                execution_time = time.time() - start_time
                
                self.registry.record_plugin_execution(plugin_name, execution_time)
                return result
        
        return None
    
    def list_active_plugins(self) -> List[str]:
        """アクティブなプラグイン一覧を取得"""
        return list(self.active_plugins.keys())
    
    def list_available_templates(self) -> List[str]:
        """利用可能なテンプレート一覧を取得"""
        templates = []
        
        for plugin_name, plugin_instance in self.active_plugins.items():
            plugin_info = self.registry.get_plugin(plugin_name)
            if plugin_info and plugin_info.metadata.layer == PluginLayer.COLORING:
                # テンプレート名を取得
                if hasattr(plugin_instance, 'template_info'):
                    template_info = plugin_instance.template_info
                    if hasattr(template_info, 'name'):
                        templates.append(template_info.name)
                    else:
                        templates.append(plugin_info.metadata.name)
                else:
                    templates.append(plugin_info.metadata.name)
        
        return templates
    
    def get_plugin_health_status(self) -> Dict[str, Any]:
        """プラグインヘルス状況を取得"""
        total_plugins = len(self.registry.plugins)
        active_plugins = len(self.active_plugins)
        error_plugins = len(self.registry.list_plugins(status=PluginStatus.ERROR))
        
        # エラー率計算
        total_executions = sum(p.execution_count for p in self.registry.plugins.values())
        total_errors = sum(p.error_count for p in self.registry.plugins.values())
        error_rate = total_errors / max(total_executions, 1)
        
        # パフォーマンス統計
        avg_execution_times = []
        for plugin_info in self.registry.plugins.values():
            if plugin_info.execution_count > 0:
                avg_execution_times.append(plugin_info.average_execution_time)
        
        avg_execution_time = sum(avg_execution_times) / len(avg_execution_times) if avg_execution_times else 0.0
        
        return {
            'total_plugins': total_plugins,
            'active_plugins': active_plugins,
            'error_plugins': error_plugins,
            'health_score': max(0, 100 - (error_rate * 100) - (error_plugins * 10)),
            'error_rate': error_rate,
            'average_execution_time': avg_execution_time,
            'plugins_directory': str(self.plugins_directory),
            'last_check': datetime.now().isoformat()
        }
    
    def export_plugin_data(self, output_path: Path):
        """プラグインデータをエクスポート"""
        try:
            health_status = self.get_plugin_health_status()
            loader_stats = self.loader.get_loader_statistics()
            registry_stats = self.registry.get_plugin_statistics()
            
            export_data = {
                'health_status': health_status,
                'loader_statistics': loader_stats,
                'registry_statistics': registry_stats,
                'active_plugins': list(self.active_plugins.keys()),
                'export_time': datetime.now().isoformat()
            }
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"📊 Plugin data exported to {output_path}")
            
        except Exception as e:
            print(f"❌ Failed to export plugin data: {str(e)}")
    
    def print_status(self):
        """プラグイン状況を表示"""
        health = self.get_plugin_health_status()
        
        print("\n" + "="*60)
        print("🔌 PLUGIN MANAGER STATUS")
        print("="*60)
        
        print(f"Health Score: {health['health_score']:.1f}/100")
        print(f"Total Plugins: {health['total_plugins']}")
        print(f"Active Plugins: {health['active_plugins']}")
        print(f"Error Plugins: {health['error_plugins']}")
        print(f"Error Rate: {health['error_rate']:.1%}")
        print(f"Avg Execution Time: {health['average_execution_time']:.3f}s")
        
        if self.active_plugins:
            print(f"\n🟢 Active Plugins:")
            for plugin_name in self.active_plugins:
                plugin_info = self.registry.get_plugin(plugin_name)
                if plugin_info:
                    print(f"  • {plugin_name} ({plugin_info.metadata.version}) - {plugin_info.metadata.layer.value}")
        
        available_templates = self.list_available_templates()
        if available_templates:
            print(f"\n🎨 Available Templates:")
            for template in available_templates:
                print(f"  • {template}")
        
        print("="*60)
    
    def save_state(self):
        """プラグインマネージャーの状態を保存"""
        self.registry.save_registry()


# グローバルプラグインマネージャーインスタンス
_global_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """グローバルプラグインマネージャーを取得"""
    global _global_plugin_manager
    if _global_plugin_manager is None:
        _global_plugin_manager = PluginManager()
    return _global_plugin_manager