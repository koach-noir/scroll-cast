"""
Plugin Validator
プラグイン検証システム
"""

import inspect
import ast
import sys
from typing import Dict, List, Any, Optional, Type, Union
from pathlib import Path
import importlib.util

from .registry import PluginMetadata, PluginCompatibility, PluginStatus
from ...interfaces import TemplateProtocol
from ...monitoring import get_monitor, MetricType


class ValidationError(Exception):
    """プラグイン検証エラー"""
    pass


class SecurityViolation(ValidationError):
    """セキュリティ違反エラー"""
    pass


class CompatibilityError(ValidationError):
    """互換性エラー"""
    pass


class PluginValidator:
    """プラグイン検証システム"""
    
    def __init__(self):
        self.monitor = get_monitor()
        
        # 禁止された import
        self.forbidden_imports = {
            'os.system', 'subprocess', 'eval', 'exec', 
            'open', '__import__', 'compile',
            'socket', 'urllib', 'requests'  # ネットワーク関連
        }
        
        # 危険な AST ノード (Python 3.8+では ast.Exec, ast.Eval は存在しない)
        self.dangerous_nodes = {
            ast.Import, ast.ImportFrom
        }
        
        # 許可されたモジュール
        self.allowed_modules = {
            'subtitle_generator', 'typing', 'dataclasses', 
            'enum', 'datetime', 'pathlib', 'json',
            'numpy', 'math', 'collections', 're'
        }
    
    def validate_plugin(self, plugin_path: Path, metadata: PluginMetadata) -> Dict[str, Any]:
        """プラグインの完全検証"""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'security_issues': [],
            'compatibility_issues': [],
            'performance_warnings': []
        }
        
        try:
            # 1. ファイル存在・構造チェック
            self._validate_file_structure(plugin_path, validation_results)
            
            # 2. メタデータ検証
            self._validate_metadata(metadata, validation_results)
            
            # 3. 互換性チェック
            self._validate_compatibility(metadata.compatibility, validation_results)
            
            # 4. セキュリティ検証
            self._validate_security(plugin_path, validation_results)
            
            # 5. Protocol準拠チェック
            self._validate_protocol_compliance(plugin_path, metadata, validation_results)
            
            # 6. パフォーマンス分析
            self._analyze_performance_implications(plugin_path, validation_results)
            
            # 検証結果判定
            if validation_results['errors'] or validation_results['security_issues']:
                validation_results['valid'] = False
            
            # メトリクス記録
            self.monitor.record_metric(
                'plugin_validation', 1.0, MetricType.QUALITY,
                {
                    'plugin_name': metadata.name,
                    'valid': validation_results['valid'],
                    'error_count': len(validation_results['errors']),
                    'warning_count': len(validation_results['warnings'])
                }
            )
            
        except Exception as e:
            validation_results['valid'] = False
            validation_results['errors'].append(f"Validation failed: {str(e)}")
        
        return validation_results
    
    def _validate_file_structure(self, plugin_path: Path, results: Dict[str, Any]):
        """ファイル構造の検証"""
        if not plugin_path.exists():
            results['errors'].append(f"Plugin path does not exist: {plugin_path}")
            return
        
        if plugin_path.is_file():
            # 単一ファイルプラグイン
            if not plugin_path.suffix == '.py':
                results['errors'].append("Plugin file must have .py extension")
        
        elif plugin_path.is_dir():
            # ディレクトリプラグイン
            required_files = ['__init__.py']
            for req_file in required_files:
                if not (plugin_path / req_file).exists():
                    results['errors'].append(f"Missing required file: {req_file}")
        
        else:
            results['errors'].append("Plugin path must be a file or directory")
    
    def _validate_metadata(self, metadata: PluginMetadata, results: Dict[str, Any]):
        """メタデータの検証"""
        # 必須フィールドチェック
        if not metadata.name:
            results['errors'].append("Plugin name is required")
        
        if not metadata.version:
            results['errors'].append("Plugin version is required")
        
        # 名前形式チェック
        if metadata.name and not metadata.name.replace('_', '').replace('-', '').isalnum():
            results['errors'].append("Plugin name must be alphanumeric with underscores/hyphens")
        
        # バージョン形式チェック（セマンティックバージョニング）
        if metadata.version:
            import re
            version_pattern = r'^\d+\.\d+\.\d+(?:-[a-zA-Z0-9]+)?$'
            if not re.match(version_pattern, metadata.version):
                results['warnings'].append("Version should follow semantic versioning (x.y.z)")
        
        # エントリーポイント検証
        if not metadata.entry_point:
            results['errors'].append("Entry point is required")
        elif not metadata.entry_point.isidentifier():
            results['errors'].append("Entry point must be a valid Python identifier")
    
    def _validate_compatibility(self, compatibility: PluginCompatibility, results: Dict[str, Any]):
        """互換性の検証"""
        # Python バージョンチェック
        current_python = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        try:
            required_python = compatibility.python_version.replace('>=', '').replace('>', '').strip()
            if self._compare_versions(current_python, required_python) < 0:
                results['compatibility_issues'].append(
                    f"Python {required_python}+ required, current: {current_python}"
                )
        except:
            results['warnings'].append("Could not parse Python version requirement")
        
        # プラットフォームチェック
        if compatibility.platform:
            import platform
            current_platform = platform.system().lower()
            if compatibility.platform.lower() != current_platform:
                results['compatibility_issues'].append(
                    f"Platform {compatibility.platform} required, current: {current_platform}"
                )
    
    def _validate_security(self, plugin_path: Path, results: Dict[str, Any]):
        """セキュリティ検証"""
        try:
            # Python ファイルの AST 解析
            python_files = []
            
            if plugin_path.is_file() and plugin_path.suffix == '.py':
                python_files = [plugin_path]
            elif plugin_path.is_dir():
                python_files = list(plugin_path.rglob('*.py'))
            
            for py_file in python_files:
                self._analyze_python_security(py_file, results)
                
        except Exception as e:
            results['security_issues'].append(f"Security analysis failed: {str(e)}")
    
    def _analyze_python_security(self, file_path: Path, results: Dict[str, Any]):
        """Python ファイルのセキュリティ分析"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # AST 解析
            tree = ast.parse(source_code)
            
            for node in ast.walk(tree):
                # 危険なノードチェック
                if type(node) in self.dangerous_nodes:
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        self._check_import_security(node, results)
                    else:
                        results['security_issues'].append(
                            f"Dangerous operation detected: {type(node).__name__}"
                        )
                
                # 危険な関数呼び出しチェック
                if isinstance(node, ast.Call):
                    self._check_function_call_security(node, results)
            
            # 文字列内での危険なパターンチェック
            dangerous_patterns = ['__import__', 'eval(', 'exec(', 'open(']
            for pattern in dangerous_patterns:
                if pattern in source_code:
                    results['security_issues'].append(
                        f"Potentially dangerous pattern found: {pattern}"
                    )
                    
        except SyntaxError as e:
            results['errors'].append(f"Syntax error in {file_path}: {str(e)}")
        except Exception as e:
            results['warnings'].append(f"Could not analyze {file_path}: {str(e)}")
    
    def _check_import_security(self, node: Union[ast.Import, ast.ImportFrom], results: Dict[str, Any]):
        """import 文のセキュリティチェック"""
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name
                if any(forbidden in module_name for forbidden in self.forbidden_imports):
                    results['security_issues'].append(
                        f"Forbidden import: {module_name}"
                    )
        
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            
            # 禁止されたモジュールチェック
            if any(forbidden in module_name for forbidden in self.forbidden_imports):
                results['security_issues'].append(
                    f"Forbidden import from: {module_name}"
                )
            
            # 許可されたモジュール以外の警告
            if module_name and not any(module_name.startswith(allowed) for allowed in self.allowed_modules):
                results['warnings'].append(
                    f"External module import: {module_name}"
                )
    
    def _check_function_call_security(self, node: ast.Call, results: Dict[str, Any]):
        """関数呼び出しのセキュリティチェック"""
        func_name = ""
        
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        
        # 危険な関数チェック
        dangerous_functions = {'eval', 'exec', 'compile', '__import__'}
        if func_name in dangerous_functions:
            results['security_issues'].append(
                f"Dangerous function call: {func_name}"
            )
    
    def _validate_protocol_compliance(self, plugin_path: Path, metadata: PluginMetadata, results: Dict[str, Any]):
        """Protocol準拠の検証"""
        try:
            # プラグインモジュールを一時的にロード
            module = self._load_plugin_module(plugin_path)
            
            # エントリーポイント関数の存在チェック
            entry_point = metadata.entry_point
            if not hasattr(module, entry_point):
                results['errors'].append(f"Entry point function '{entry_point}' not found")
                return
            
            # エントリーポイント関数を呼び出し
            entry_func = getattr(module, entry_point)
            if not callable(entry_func):
                results['errors'].append(f"Entry point '{entry_point}' is not callable")
                return
            
            # プラグインインスタンスを取得
            try:
                plugin_instance = entry_func()
            except Exception as e:
                results['errors'].append(f"Failed to create plugin instance: {str(e)}")
                return
            
            # 層別のProtocol準拠チェック
            if metadata.layer.value == 'coloring':
                self._validate_template_protocol(plugin_instance, results)
            
        except Exception as e:
            results['errors'].append(f"Protocol validation failed: {str(e)}")
    
    def _validate_template_protocol(self, plugin_instance: Any, results: Dict[str, Any]):
        """TemplateProtocol準拠の検証"""
        required_methods = [
            'get_parameters', 'get_default_parameters', 'validate_parameters',
            'generate_ass_from_formatted', 'calculate_total_duration'
        ]
        
        for method_name in required_methods:
            if not hasattr(plugin_instance, method_name):
                results['errors'].append(f"Missing required method: {method_name}")
                continue
            
            method = getattr(plugin_instance, method_name)
            if not callable(method):
                results['errors'].append(f"Method {method_name} is not callable")
                continue
            
            # メソッドシグネチャチェック
            try:
                sig = inspect.signature(method)
                # 基本的なシグネチャ検証
                if method_name == 'generate_ass_from_formatted':
                    # 必須パラメータのチェック
                    params = list(sig.parameters.keys())
                    if len(params) < 2:  # self + formatted_text 最低限
                        results['warnings'].append(
                            f"Method {method_name} may have incorrect signature"
                        )
            except Exception:
                results['warnings'].append(f"Could not analyze signature for {method_name}")
        
        # テンプレート固有のチェック
        try:
            # パラメータ取得テスト
            params = plugin_instance.get_parameters()
            if not isinstance(params, list):
                results['errors'].append("get_parameters() must return a list")
            
            # デフォルトパラメータ取得テスト
            defaults = plugin_instance.get_default_parameters()
            if not isinstance(defaults, dict):
                results['errors'].append("get_default_parameters() must return a dict")
            
        except Exception as e:
            results['warnings'].append(f"Template method test failed: {str(e)}")
    
    def _analyze_performance_implications(self, plugin_path: Path, results: Dict[str, Any]):
        """パフォーマンスへの影響分析"""
        try:
            # ファイルサイズチェック
            if plugin_path.is_file():
                file_size = plugin_path.stat().st_size
                if file_size > 1024 * 1024:  # 1MB
                    results['performance_warnings'].append(
                        f"Large plugin file size: {file_size / 1024 / 1024:.1f}MB"
                    )
            
            # コード複雑度の簡易チェック
            python_files = []
            if plugin_path.is_file() and plugin_path.suffix == '.py':
                python_files = [plugin_path]
            elif plugin_path.is_dir():
                python_files = list(plugin_path.rglob('*.py'))
            
            for py_file in python_files:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                
                # 行数チェック
                line_count = len(source_code.splitlines())
                if line_count > 1000:
                    results['performance_warnings'].append(
                        f"Large file: {py_file.name} ({line_count} lines)"
                    )
                
                # ループの深さチェック（簡易）
                nested_loops = source_code.count('for ') + source_code.count('while ')
                if nested_loops > 10:
                    results['performance_warnings'].append(
                        f"Many loops detected in {py_file.name}"
                    )
                    
        except Exception as e:
            results['warnings'].append(f"Performance analysis failed: {str(e)}")
    
    def _load_plugin_module(self, plugin_path: Path):
        """プラグインモジュールを一時的にロード"""
        if plugin_path.is_file():
            spec = importlib.util.spec_from_file_location("temp_plugin", plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        
        elif plugin_path.is_dir():
            init_file = plugin_path / "__init__.py"
            if init_file.exists():
                spec = importlib.util.spec_from_file_location("temp_plugin", init_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
        
        raise ValidationError(f"Could not load module from {plugin_path}")
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """バージョン比較（簡易実装）"""
        def version_tuple(v):
            return tuple(map(int, v.split('.')))
        
        v1_tuple = version_tuple(version1)
        v2_tuple = version_tuple(version2)
        
        if v1_tuple < v2_tuple:
            return -1
        elif v1_tuple > v2_tuple:
            return 1
        else:
            return 0
    
    def validate_quick(self, plugin_path: Path, metadata: PluginMetadata) -> bool:
        """クイック検証（基本チェックのみ）"""
        try:
            # 基本的なチェックのみ実行
            if not plugin_path.exists():
                return False
            
            if not metadata.name or not metadata.version:
                return False
            
            # エントリーポイントの存在チェック
            module = self._load_plugin_module(plugin_path)
            if not hasattr(module, metadata.entry_point):
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_validation_summary(self, validation_results: Dict[str, Any]) -> str:
        """検証結果のサマリーを生成"""
        if validation_results['valid']:
            status = "✅ VALID"
        else:
            status = "❌ INVALID"
        
        summary_lines = [f"Plugin Validation: {status}"]
        
        if validation_results['errors']:
            summary_lines.append(f"Errors: {len(validation_results['errors'])}")
            for error in validation_results['errors'][:3]:  # 最初の3つのみ
                summary_lines.append(f"  - {error}")
        
        if validation_results['security_issues']:
            summary_lines.append(f"Security Issues: {len(validation_results['security_issues'])}")
            for issue in validation_results['security_issues'][:3]:
                summary_lines.append(f"  - {issue}")
        
        if validation_results['warnings']:
            summary_lines.append(f"Warnings: {len(validation_results['warnings'])}")
        
        return "\n".join(summary_lines)