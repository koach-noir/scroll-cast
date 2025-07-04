"""
External Configuration Manager
外部設定ファイル管理システム
"""

import os
import json
import yaml
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Union
from threading import Lock
from pydantic import BaseModel, Field

# Optional dependency for file watching
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    Observer = None
    FileSystemEventHandler = None
    FileModifiedEvent = None
    WATCHDOG_AVAILABLE = False


class ExternalConfigSchema(BaseModel):
    """外部設定ファイルのスキーマ"""
    file_path: str = Field(..., description="設定ファイルパス")
    format: str = Field(default="auto", description="ファイル形式 (yaml/json/auto)")
    watch_changes: bool = Field(default=True, description="変更監視の有効化")
    reload_delay: float = Field(default=0.5, description="リロード遅延（秒）")
    validation_callback: Optional[str] = Field(default=None, description="検証コールバック名")


class ConfigChangeEvent:
    """設定変更イベント"""
    def __init__(self, file_path: str, old_config: Dict[str, Any], new_config: Dict[str, Any]):
        self.file_path = file_path
        self.old_config = old_config
        self.new_config = new_config
        self.timestamp = time.time()


class ConfigFileWatcher:
    """設定ファイル変更監視"""
    
    def __init__(self, config_manager: 'ExternalConfigManager'):
        self.config_manager = config_manager
        self.debounce_delay = 0.5
        self.last_modified = {}
        
        if WATCHDOG_AVAILABLE:
            # FileSystemEventHandlerを継承
            class WatchdogHandler(FileSystemEventHandler):
                def __init__(self, watcher):
                    self.watcher = watcher
                
                def on_modified(self, event):
                    self.watcher.on_modified(event)
            
            self.handler = WatchdogHandler(self)
        else:
            self.handler = None
    
    def on_modified(self, event):
        if not WATCHDOG_AVAILABLE or event.is_directory:
            return
        
        file_path = event.src_path
        current_time = time.time()
        
        # デバウンス処理
        if file_path in self.last_modified:
            if current_time - self.last_modified[file_path] < self.debounce_delay:
                return
        
        self.last_modified[file_path] = current_time
        self.config_manager._handle_file_change(file_path)


class ExternalConfigManager:
    """外部設定ファイル管理クラス"""
    
    def __init__(self, base_config_dir: Optional[str] = None):
        """
        Args:
            base_config_dir: 基本設定ディレクトリ
        """
        self.base_config_dir = Path(base_config_dir) if base_config_dir else Path("config")
        self.base_config_dir.mkdir(exist_ok=True)
        
        # 設定ファイル管理
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._config_schemas: Dict[str, ExternalConfigSchema] = {}
        self._config_timestamps: Dict[str, float] = {}
        self._config_lock = Lock()
        
        # 変更監視
        self._observer = Observer() if WATCHDOG_AVAILABLE else None
        self._file_watcher = ConfigFileWatcher(self)
        self._change_callbacks: Dict[str, List[Callable]] = {}
        
        # 監視開始
        self._start_watching()
    
    def register_config_file(self, 
                           config_id: str, 
                           file_path: str, 
                           schema: Optional[ExternalConfigSchema] = None,
                           load_immediately: bool = True) -> bool:
        """外部設定ファイルを登録"""
        try:
            # スキーマのデフォルト設定
            if schema is None:
                schema = ExternalConfigSchema(file_path=file_path)
            
            # 絶対パスに変換
            if not Path(file_path).is_absolute():
                file_path = str(self.base_config_dir / file_path)
            
            schema.file_path = file_path
            
            with self._config_lock:
                self._config_schemas[config_id] = schema
            
            # 監視対象ディレクトリを追加
            if schema.watch_changes and WATCHDOG_AVAILABLE and self._observer:
                watch_dir = Path(file_path).parent
                if watch_dir.exists():
                    try:
                        self._observer.schedule(self._file_watcher.handler, str(watch_dir), recursive=False)
                    except Exception:
                        pass  # 既に監視中の場合は無視
            
            # 即座に読み込み
            if load_immediately:
                self.load_config(config_id)
            
            print(f"✅ External config registered: '{config_id}' -> {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to register config file '{config_id}': {e}")
            return False
    
    def load_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        """設定ファイルを読み込み"""
        try:
            schema = self._config_schemas.get(config_id)
            if not schema:
                print(f"⚠️ Config schema not found for '{config_id}'")
                return None
            
            file_path = Path(schema.file_path)
            
            # ファイル存在チェック
            if not file_path.exists():
                print(f"⚠️ Config file not found: {file_path}")
                return None
            
            # タイムスタンプチェック
            current_timestamp = file_path.stat().st_mtime
            cached_timestamp = self._config_timestamps.get(config_id)
            
            if cached_timestamp == current_timestamp and config_id in self._configs:
                return self._configs[config_id]
            
            # ファイル読み込み
            config_data = self._load_file(file_path, schema.format)
            if config_data is None:
                return None
            
            # 検証
            if schema.validation_callback:
                validation_func = self._get_validation_callback(schema.validation_callback)
                if validation_func:
                    validation_result = validation_func(config_data)
                    if not validation_result.get('valid', True):
                        print(f"❌ Config validation failed for '{config_id}': {validation_result.get('errors', [])}")
                        return None
            
            # キャッシュ更新
            with self._config_lock:
                old_config = self._configs.get(config_id, {})
                self._configs[config_id] = config_data
                self._config_timestamps[config_id] = current_timestamp
            
            # 変更通知
            if old_config != config_data:
                self._notify_config_change(config_id, old_config, config_data)
            
            return config_data
            
        except Exception as e:
            print(f"❌ Failed to load config '{config_id}': {e}")
            return None
    
    def _load_file(self, file_path: Path, format_hint: str) -> Optional[Dict[str, Any]]:
        """ファイルを読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # フォーマット判定
                if format_hint == "auto":
                    if file_path.suffix in ['.yaml', '.yml']:
                        format_hint = "yaml"
                    elif file_path.suffix == '.json':
                        format_hint = "json"
                    else:
                        # 内容から判定
                        content = f.read()
                        f.seek(0)
                        if content.strip().startswith(('{', '[')):
                            format_hint = "json"
                        else:
                            format_hint = "yaml"
                
                # 読み込み
                if format_hint == "yaml":
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
                    
        except Exception as e:
            print(f"❌ Failed to load file '{file_path}': {e}")
            return None
    
    def get_config(self, config_id: str, reload_if_changed: bool = True) -> Optional[Dict[str, Any]]:
        """設定を取得"""
        if reload_if_changed:
            return self.load_config(config_id)
        else:
            return self._configs.get(config_id)
    
    def get_config_value(self, config_id: str, key_path: str, default: Any = None) -> Any:
        """設定値を取得（ドット記法対応）"""
        config = self.get_config(config_id)
        if not config:
            return default
        
        # ドット記法で階層アクセス
        keys = key_path.split('.')
        value = config
        
        try:
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            return value
        except Exception:
            return default
    
    def watch_config_changes(self, config_id: str, callback: Callable[[ConfigChangeEvent], None]):
        """設定変更の監視コールバックを登録"""
        if config_id not in self._change_callbacks:
            self._change_callbacks[config_id] = []
        self._change_callbacks[config_id].append(callback)
    
    def _handle_file_change(self, file_path: str):
        """ファイル変更の処理"""
        # 該当する設定IDを検索
        for config_id, schema in self._config_schemas.items():
            if schema.file_path == file_path:
                print(f"🔄 Config file changed: '{config_id}' ({file_path})")
                
                # 遅延リロード
                if schema.reload_delay > 0:
                    time.sleep(schema.reload_delay)
                
                self.load_config(config_id)
                break
    
    def _notify_config_change(self, config_id: str, old_config: Dict[str, Any], new_config: Dict[str, Any]):
        """設定変更を通知"""
        if config_id in self._change_callbacks:
            event = ConfigChangeEvent(
                self._config_schemas[config_id].file_path,
                old_config,
                new_config
            )
            
            for callback in self._change_callbacks[config_id]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"⚠️ Config change callback error: {e}")
    
    def _get_validation_callback(self, callback_name: str) -> Optional[Callable]:
        """検証コールバックを取得"""
        # 組み込み検証関数
        builtin_validators = {
            'basic_validation': self._basic_validation,
            'parameter_validation': self._parameter_validation
        }
        
        return builtin_validators.get(callback_name)
    
    def _basic_validation(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """基本的な検証"""
        if not isinstance(config_data, dict):
            return {'valid': False, 'errors': ['Config must be a dictionary']}
        return {'valid': True}
    
    def _parameter_validation(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """パラメータ検証"""
        errors = []
        
        # 必須フィールドチェック
        required_fields = ['parameters']
        for field in required_fields:
            if field not in config_data:
                errors.append(f"Missing required field: {field}")
        
        # パラメータ型チェック
        if 'parameters' in config_data:
            params = config_data['parameters']
            if not isinstance(params, dict):
                errors.append("'parameters' must be a dictionary")
            else:
                for key, value in params.items():
                    if not isinstance(key, str):
                        errors.append(f"Parameter key must be string: {key}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _start_watching(self):
        """ファイル監視を開始"""
        if not WATCHDOG_AVAILABLE:
            print("⚠️ Watchdog not available, file watching disabled")
            return
        
        try:
            if self._observer:
                self._observer.start()
                print("👁️ Config file watching started")
        except Exception as e:
            print(f"⚠️ Failed to start config file watching: {e}")
    
    def stop_watching(self):
        """ファイル監視を停止"""
        if not WATCHDOG_AVAILABLE or not self._observer:
            return
        
        try:
            self._observer.stop()
            self._observer.join()
            print("👁️ Config file watching stopped")
        except Exception as e:
            print(f"⚠️ Failed to stop config file watching: {e}")
    
    def reload_all_configs(self) -> int:
        """すべての設定ファイルを再読み込み"""
        success_count = 0
        
        for config_id in list(self._config_schemas.keys()):
            if self.load_config(config_id) is not None:
                success_count += 1
        
        print(f"🔄 Reloaded {success_count}/{len(self._config_schemas)} config files")
        return success_count
    
    def list_registered_configs(self) -> List[Dict[str, Any]]:
        """登録済み設定一覧を取得"""
        configs = []
        
        for config_id, schema in self._config_schemas.items():
            config_info = {
                'id': config_id,
                'file_path': schema.file_path,
                'format': schema.format,
                'watch_changes': schema.watch_changes,
                'loaded': config_id in self._configs,
                'last_modified': self._config_timestamps.get(config_id)
            }
            configs.append(config_info)
        
        return configs
    
    def export_config(self, config_id: str, export_path: str, format: str = "yaml") -> bool:
        """設定をエクスポート"""
        try:
            config_data = self.get_config(config_id)
            if not config_data:
                print(f"⚠️ Config not found: '{config_id}'")
                return False
            
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                if format.lower() == "yaml":
                    yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Config exported: '{config_id}' -> {export_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to export config '{config_id}': {e}")
            return False
    
    def get_manager_status(self) -> Dict[str, Any]:
        """マネージャーの状態を取得"""
        return {
            'registered_configs': len(self._config_schemas),
            'loaded_configs': len(self._configs),
            'watching_enabled': WATCHDOG_AVAILABLE and self._observer and self._observer.is_alive(),
            'base_config_dir': str(self.base_config_dir),
            'change_callbacks': sum(len(callbacks) for callbacks in self._change_callbacks.values())
        }
    
    def __del__(self):
        """デストラクタ"""
        try:
            self.stop_watching()
        except Exception:
            pass