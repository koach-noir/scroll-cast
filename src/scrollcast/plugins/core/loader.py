"""
Plugin Loader
プラグイン動的ローダーシステム
"""

import sys
import time
import importlib
import importlib.util
from pathlib import Path
from typing import Any, Optional, Dict, List
from datetime import datetime
import toml

from .registry import PluginMetadata, PluginInfo, PluginStatus, PluginLayer, PluginCompatibility, PluginDependency
from .validator import PluginValidator
from ...monitoring import get_monitor, MetricType


class PluginLoadError(Exception):
    """プラグインロードエラー"""
    pass


class MetadataParseError(PluginLoadError):
    """メタデータ解析エラー"""
    pass


class PluginLoader:
    """プラグイン動的ローダー"""
    
    def __init__(self, validator: Optional[PluginValidator] = None):
        self.validator = validator or PluginValidator()
        self.monitor = get_monitor()
        self.loaded_modules: Dict[str, Any] = {}
        
    def load_plugin_from_path(self, plugin_path: Path) -> PluginInfo:
        """パスからプラグインをロード"""
        start_time = time.time()
        
        try:
            # 1. メタデータ読み込み
            metadata = self.load_metadata(plugin_path)
            
            # 2. プラグイン情報作成
            plugin_info = PluginInfo(
                metadata=metadata,
                path=plugin_path,
                status=PluginStatus.LOADING,
                load_time=datetime.now()
            )
            
            # 3. 検証実行
            validation_results = self.validator.validate_plugin(plugin_path, metadata)
            if not validation_results['valid']:
                error_msg = f"Validation failed: {', '.join(validation_results['errors'])}"
                plugin_info.record_error(error_msg)
                raise PluginLoadError(error_msg)
            
            # 4. プラグインモジュールロード
            plugin_module = self._load_module(plugin_path, metadata.name)
            
            # 5. プラグインインスタンス作成
            plugin_instance = self._create_plugin_instance(plugin_module, metadata)
            
            # 6. ロード完了
            plugin_info.status = PluginStatus.LOADED
            plugin_info.load_duration = time.time() - start_time
            
            # メトリクス記録
            self.monitor.record_metric(
                'plugin_loaded', 1.0, MetricType.BUSINESS,
                {
                    'plugin_name': metadata.name,
                    'layer': metadata.layer.value,
                    'load_time': plugin_info.load_duration
                }
            )
            
            print(f"✅ Plugin '{metadata.name}' loaded successfully in {plugin_info.load_duration:.3f}s")
            return plugin_info
            
        except Exception as e:
            load_duration = time.time() - start_time
            error_msg = f"Failed to load plugin from {plugin_path}: {str(e)}"
            
            # エラーメトリクス記録
            self.monitor.record_metric(
                'plugin_load_failed', 1.0, MetricType.SYSTEM,
                {'plugin_path': str(plugin_path), 'error': str(e), 'load_time': load_duration}
            )
            
            print(f"❌ {error_msg}")
            raise PluginLoadError(error_msg)
    
    def load_metadata(self, plugin_path: Path) -> PluginMetadata:
        """プラグインメタデータを読み込み"""
        metadata_file = None
        
        # メタデータファイル検索
        if plugin_path.is_file():
            # 同じディレクトリの plugin.toml
            metadata_file = plugin_path.parent / "plugin.toml"
        elif plugin_path.is_dir():
            # ディレクトリ内の plugin.toml
            metadata_file = plugin_path / "plugin.toml"
        
        if not metadata_file or not metadata_file.exists():
            # デフォルトメタデータ生成
            return self._generate_default_metadata(plugin_path)
        
        try:
            return self._parse_metadata_file(metadata_file)
        except Exception as e:
            raise MetadataParseError(f"Failed to parse {metadata_file}: {str(e)}")
    
    def _parse_metadata_file(self, metadata_file: Path) -> PluginMetadata:
        """メタデータファイルを解析"""
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = toml.load(f)
            
            # 基本情報
            plugin_section = data.get('plugin', {})
            name = plugin_section.get('name', metadata_file.parent.name)
            version = plugin_section.get('version', '1.0.0')
            description = plugin_section.get('description', '')
            author = plugin_section.get('author', '')
            license = plugin_section.get('license', 'MIT')
            homepage = plugin_section.get('homepage', '')
            layer = PluginLayer(plugin_section.get('layer', 'coloring'))
            entry_point = plugin_section.get('entry_point', 'get_plugin')
            
            # 互換性情報
            compatibility_section = data.get('compatibility', {})
            compatibility = PluginCompatibility(
                subtitle_generator_version=compatibility_section.get('subtitle_generator_version', '>=1.0.0'),
                python_version=compatibility_section.get('python_version', '>=3.8.0'),
                platform=compatibility_section.get('platform')
            )
            
            # 依存関係
            dependencies_section = data.get('dependencies', {})
            dependencies = []
            for dep_name, dep_info in dependencies_section.items():
                if isinstance(dep_info, str):
                    # シンプルなバージョン指定
                    dependencies.append(PluginDependency(
                        name=dep_name,
                        version_requirement=dep_info
                    ))
                elif isinstance(dep_info, dict):
                    # 詳細な依存関係情報
                    dependencies.append(PluginDependency(
                        name=dep_name,
                        version_requirement=dep_info.get('version', '*'),
                        optional=dep_info.get('optional', False),
                        description=dep_info.get('description', '')
                    ))
            
            # 設定スキーマ
            configuration_schema = data.get('configuration', {})
            
            return PluginMetadata(
                name=name,
                version=version,
                description=description,
                author=author,
                license=license,
                homepage=homepage,
                layer=layer,
                entry_point=entry_point,
                compatibility=compatibility,
                dependencies=dependencies,
                configuration_schema=configuration_schema
            )
            
        except Exception as e:
            raise MetadataParseError(f"Invalid metadata format: {str(e)}")
    
    def _generate_default_metadata(self, plugin_path: Path) -> PluginMetadata:
        """デフォルトメタデータを生成"""
        if plugin_path.is_file():
            name = plugin_path.stem
        else:
            name = plugin_path.name
        
        return PluginMetadata(
            name=name,
            version="1.0.0",
            description=f"Plugin: {name}",
            author="Unknown",
            layer=PluginLayer.COLORING  # デフォルトは coloring層
        )
    
    def _load_module(self, plugin_path: Path, module_name: str) -> Any:
        """プラグインモジュールをロード"""
        try:
            if plugin_path.is_file():
                # 単一ファイルプラグイン
                spec = importlib.util.spec_from_file_location(module_name, plugin_path)
                module = importlib.util.module_from_spec(spec)
                
                # モジュールを sys.modules に追加
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
            elif plugin_path.is_dir():
                # ディレクトリプラグイン
                init_file = plugin_path / "__init__.py"
                if not init_file.exists():
                    raise PluginLoadError(f"Directory plugin missing __init__.py: {plugin_path}")
                
                spec = importlib.util.spec_from_file_location(module_name, init_file)
                module = importlib.util.module_from_spec(spec)
                
                # モジュールを sys.modules に追加
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
            
            else:
                raise PluginLoadError(f"Invalid plugin path: {plugin_path}")
            
            # ロード済みモジュールを記録
            self.loaded_modules[module_name] = module
            return module
            
        except Exception as e:
            raise PluginLoadError(f"Failed to load module {module_name}: {str(e)}")
    
    def _create_plugin_instance(self, module: Any, metadata: PluginMetadata) -> Any:
        """プラグインインスタンスを作成"""
        entry_point = metadata.entry_point
        
        if not hasattr(module, entry_point):
            raise PluginLoadError(f"Entry point '{entry_point}' not found in module")
        
        entry_func = getattr(module, entry_point)
        if not callable(entry_func):
            raise PluginLoadError(f"Entry point '{entry_point}' is not callable")
        
        try:
            plugin_instance = entry_func()
            return plugin_instance
        except Exception as e:
            raise PluginLoadError(f"Failed to create plugin instance: {str(e)}")
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """プラグインをアンロード"""
        try:
            # sys.modules からモジュールを削除
            if plugin_name in sys.modules:
                del sys.modules[plugin_name]
            
            # ロード済みモジュールから削除
            if plugin_name in self.loaded_modules:
                del self.loaded_modules[plugin_name]
            
            # メトリクス記録
            self.monitor.record_metric(
                'plugin_unloaded', 1.0, MetricType.BUSINESS,
                {'plugin_name': plugin_name}
            )
            
            print(f"✅ Plugin '{plugin_name}' unloaded")
            return True
            
        except Exception as e:
            print(f"❌ Failed to unload plugin '{plugin_name}': {str(e)}")
            return False
    
    def reload_plugin(self, plugin_info: PluginInfo) -> PluginInfo:
        """プラグインをリロード"""
        plugin_name = plugin_info.metadata.name
        
        try:
            # 1. 既存プラグインをアンロード
            self.unload_plugin(plugin_name)
            
            # 2. プラグインを再ロード
            new_plugin_info = self.load_plugin_from_path(plugin_info.path)
            
            print(f"🔄 Plugin '{plugin_name}' reloaded")
            return new_plugin_info
            
        except Exception as e:
            error_msg = f"Failed to reload plugin '{plugin_name}': {str(e)}"
            plugin_info.record_error(error_msg)
            print(f"❌ {error_msg}")
            raise PluginLoadError(error_msg)
    
    def scan_plugins_directory(self, directory: Path) -> List[Path]:
        """プラグインディレクトリをスキャン"""
        if not directory.exists() or not directory.is_dir():
            return []
        
        plugin_paths = []
        
        try:
            for item in directory.iterdir():
                if item.is_file() and item.suffix == '.py':
                    # 単一ファイルプラグイン
                    plugin_paths.append(item)
                elif item.is_dir() and (item / "__init__.py").exists():
                    # ディレクトリプラグイン
                    plugin_paths.append(item)
            
            print(f"📁 Found {len(plugin_paths)} plugins in {directory}")
            return plugin_paths
            
        except Exception as e:
            print(f"❌ Failed to scan directory {directory}: {str(e)}")
            return []
    
    def load_plugins_from_directory(self, directory: Path) -> List[PluginInfo]:
        """ディレクトリから全プラグインをロード"""
        plugin_paths = self.scan_plugins_directory(directory)
        loaded_plugins = []
        
        for plugin_path in plugin_paths:
            try:
                plugin_info = self.load_plugin_from_path(plugin_path)
                loaded_plugins.append(plugin_info)
            except PluginLoadError as e:
                print(f"⚠️ Skipped plugin {plugin_path}: {str(e)}")
                continue
        
        print(f"✅ Loaded {len(loaded_plugins)}/{len(plugin_paths)} plugins from {directory}")
        return loaded_plugins
    
    def validate_dependencies(self, metadata: PluginMetadata) -> Dict[str, Any]:
        """依存関係を検証"""
        validation_result = {
            'valid': True,
            'missing_dependencies': [],
            'version_conflicts': [],
            'warnings': []
        }
        
        for dependency in metadata.dependencies:
            try:
                # モジュールの存在チェック
                importlib.import_module(dependency.name)
                
                # バージョンチェック（可能な場合）
                try:
                    module = importlib.import_module(dependency.name)
                    if hasattr(module, '__version__'):
                        module_version = module.__version__
                        # 簡易バージョン比較
                        if not self._check_version_requirement(module_version, dependency.version_requirement):
                            validation_result['version_conflicts'].append(
                                f"{dependency.name}: requires {dependency.version_requirement}, "
                                f"found {module_version}"
                            )
                except:
                    validation_result['warnings'].append(
                        f"Could not check version for {dependency.name}"
                    )
                    
            except ImportError:
                if not dependency.optional:
                    validation_result['missing_dependencies'].append(dependency.name)
                    validation_result['valid'] = False
                else:
                    validation_result['warnings'].append(
                        f"Optional dependency not found: {dependency.name}"
                    )
        
        return validation_result
    
    def _check_version_requirement(self, version: str, requirement: str) -> bool:
        """バージョン要件チェック（簡易実装）"""
        # 簡易的な実装 - 実際にはより厳密な解析が必要
        if requirement == '*':
            return True
        
        if requirement.startswith('>='):
            required_version = requirement[2:].strip()
            return self._compare_versions(version, required_version) >= 0
        elif requirement.startswith('>'):
            required_version = requirement[1:].strip()
            return self._compare_versions(version, required_version) > 0
        elif requirement.startswith('=='):
            required_version = requirement[2:].strip()
            return version == required_version
        
        return True
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """バージョン比較"""
        def version_tuple(v):
            return tuple(map(int, v.split('.')[:3]))  # major.minor.patch のみ
        
        try:
            v1_tuple = version_tuple(version1)
            v2_tuple = version_tuple(version2)
            
            if v1_tuple < v2_tuple:
                return -1
            elif v1_tuple > v2_tuple:
                return 1
            else:
                return 0
        except:
            return 0  # 解析失敗時は等しいとみなす
    
    def get_loader_statistics(self) -> Dict[str, Any]:
        """ローダー統計を取得"""
        return {
            'loaded_modules': len(self.loaded_modules),
            'module_names': list(self.loaded_modules.keys()),
            'loader_active': True
        }