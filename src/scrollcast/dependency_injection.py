"""
Dependency Injection Container
依存性注入コンテナの実装
"""

from typing import Dict, Type, TypeVar, Optional, Any, Callable, List
import threading
import time
from abc import ABC, abstractmethod

from .interfaces import (
    ServiceContainerProtocol,
    TemplateEngineProtocol,
    TextFormatterProtocol,
    VideoGeneratorProtocol,
    ASSBuilderProtocol,
    TemplateProtocol,
    TemplateFactoryProtocol,
    ServiceFactoryProtocol,
    ErrorHandlerProtocol,
    ConfigurationProtocol
)
from .monitoring import get_monitor, get_quality_monitor, MetricType

T = TypeVar('T')


class ServiceContainer:
    """依存性注入サービスコンテナ"""
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable[[], Any]] = {}
        self._lock = threading.RLock()
    
    def register_singleton(self, service_type: Type[T], instance: T) -> None:
        """シングルトンサービスを登録
        
        Args:
            service_type: サービスの型
            instance: サービスのインスタンス
        """
        with self._lock:
            self._singletons[service_type] = instance
    
    def register_transient(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """一時的サービスを登録（呼び出し毎に新しいインスタンス）
        
        Args:
            service_type: サービスの型
            factory: インスタンス生成関数
        """
        with self._lock:
            self._factories[service_type] = factory
    
    def register_implementation(self, service_type: Type[T], implementation_type: Type[T]) -> None:
        """実装クラスを登録
        
        Args:
            service_type: サービスの型
            implementation_type: 実装クラスの型
        """
        with self._lock:
            self._services[service_type] = implementation_type
    
    def get(self, service_type: Type[T]) -> T:
        """サービスを取得
        
        Args:
            service_type: 取得するサービスの型
        
        Returns:
            サービスのインスタンス
        
        Raises:
            ValueError: サービスが登録されていない場合
        """
        with self._lock:
            # メトリクス記録
            monitor = get_monitor()
            start_time = time.time()
            
            try:
                # シングルトンチェック
                if service_type in self._singletons:
                    result = self._singletons[service_type]
                    resolve_time = time.time() - start_time
                    monitor.record_metric(
                        'service_resolve_time', resolve_time * 1000, MetricType.PERFORMANCE,
                        {'service_type': service_type.__name__, 'resolve_type': 'singleton'}
                    )
                    return result
                
                # ファクトリーチェック
                if service_type in self._factories:
                    result = self._factories[service_type]()
                    resolve_time = time.time() - start_time
                    monitor.record_metric(
                        'service_resolve_time', resolve_time * 1000, MetricType.PERFORMANCE,
                        {'service_type': service_type.__name__, 'resolve_type': 'factory'}
                    )
                    return result
                
                # 実装チェック
                if service_type in self._services:
                    implementation_type = self._services[service_type]
                    result = implementation_type()
                    resolve_time = time.time() - start_time
                    monitor.record_metric(
                        'service_resolve_time', resolve_time * 1000, MetricType.PERFORMANCE,
                        {'service_type': service_type.__name__, 'resolve_type': 'implementation'}
                    )
                    return result
                
                # サービス未登録エラー
                monitor.record_metric(
                    'service_resolve_error', 1.0, MetricType.SYSTEM,
                    {'service_type': service_type.__name__, 'error': 'not_registered'}
                )
                raise ValueError(f"Service of type {service_type} is not registered")
                
            except Exception as e:
                resolve_time = time.time() - start_time
                monitor.record_metric(
                    'service_resolve_error', 1.0, MetricType.SYSTEM,
                    {'service_type': service_type.__name__, 'error': str(e), 'resolve_time': resolve_time * 1000}
                )
                raise
    
    def is_registered(self, service_type: Type[T]) -> bool:
        """サービスが登録されているかチェック
        
        Args:
            service_type: チェックするサービスの型
        
        Returns:
            登録されている場合True
        """
        with self._lock:
            return (service_type in self._singletons or 
                   service_type in self._factories or 
                   service_type in self._services)
    
    def clear(self) -> None:
        """全サービスを削除"""
        with self._lock:
            self._services.clear()
            self._singletons.clear()
            self._factories.clear()


class ServiceFactory:
    """サービスファクトリー"""
    
    def __init__(self, container: ServiceContainer):
        self.container = container
    
    def create_text_formatter(self, config=None) -> TextFormatterProtocol:
        """テキストフォーマッターを作成"""
        from .boxing.text_formatter import TextFormatter
        from .boxing.display_config import DisplayConfig
        
        if config is None:
            config = DisplayConfig.create_mobile_portrait()
        
        return TextFormatter(config)
    
    def create_video_generator(self, resolution=(1080, 1920)) -> VideoGeneratorProtocol:
        """動画ジェネレーターを作成"""
        from .rendering.video_generator import VideoGenerator
        return VideoGenerator(default_resolution=resolution)
    
    def create_ass_builder(self, title="Subtitle") -> ASSBuilderProtocol:
        """ASSビルダーを作成"""
        from .packing.ass_builder import ASSBuilder
        return ASSBuilder(title=title)
    
    def create_template(self, template_type: str) -> Optional[TemplateProtocol]:
        """テンプレートを作成"""
        template_map = {
            'typewriter_fade': self._create_typewriter_fade,
            'railway_scroll': self._create_railway_scroll,
            'simple_role': self._create_simple_role,
        }
        
        factory = template_map.get(template_type)
        if factory:
            return factory()
        return None
    
    def _create_typewriter_fade(self) -> TemplateProtocol:
        """TypewriterFadeテンプレートを作成"""
        from .coloring.typewriter_fade import TypewriterFadeTemplate
        return TypewriterFadeTemplate()
    
    def _create_railway_scroll(self) -> TemplateProtocol:
        """RailwayScrollテンプレートを作成"""
        from .coloring.railway_scroll import RailwayScrollTemplate
        return RailwayScrollTemplate()
    
    def _create_simple_role(self) -> TemplateProtocol:
        """SimpleRoleテンプレートを作成"""
        from .coloring.simple_role import SimpleRoleTemplate
        return SimpleRoleTemplate()


class Configuration:
    """設定管理クラス"""
    
    def __init__(self):
        self._settings = {
            'default_resolution': (1080, 1920),
            'quality_settings': {
                'crf': 23,
                'preset': 'fast',
                'fps': 30
            },
            'template_settings': {
                'typewriter_fade': {
                    'char_interval': 0.15,
                    'fade_duration': 0.1,
                    'pause_between_lines': 1.0,
                    'pause_between_paragraphs': 2.0
                },
                'railway_scroll': {
                    'fade_in_duration': 0.8,
                    'pause_duration': 2.0,
                    'fade_out_duration': 0.8,
                    'overlap_duration': 0.4,
                    'empty_line_pause': 1.0
                }
            }
        }
    
    def get_default_resolution(self):
        return self._settings['default_resolution']
    
    def get_quality_settings(self):
        return self._settings['quality_settings']
    
    def get_template_settings(self, template_name: str):
        return self._settings['template_settings'].get(template_name, {})


class ErrorHandler:
    """エラーハンドラー"""
    
    def handle_generation_error(self, error: Exception, context: Dict[str, Any]):
        """生成エラーを処理"""
        from .models.output_models import GenerationResult, ASSOutput, VideoOutput
        
        error_message = f"Generation failed: {str(error)}"
        print(f"❌ {error_message}")
        
        if context.get('verbose', False):
            import traceback
            print(traceback.format_exc())
        
        result = GenerationResult(
            success=False,
            ass_output=None,
            video_output=None,
            template_name=context.get('template_name', 'unknown')
        )
        result.add_error("generation_error", error_message)
        return result
    
    def log_error(self, error: Exception, details: str) -> None:
        """エラーをログ出力"""
        print(f"❌ Error: {details}")
        print(f"Exception: {str(error)}")


class DependencyInjectedTemplateEngine:
    """依存性注入版テンプレートエンジン"""
    
    def __init__(self, container: ServiceContainer):
        self.container = container
        self.factory = ServiceFactory(container)
        self.config = Configuration()
        self.error_handler = ErrorHandler()
        self._templates: Dict[str, TemplateProtocol] = {}
        
        # デフォルトテンプレートを初期化
        self._initialize_templates()
    
    def _initialize_templates(self):
        """テンプレートを初期化"""
        template_types = ['typewriter_fade', 'railway_scroll', 'simple_role']
        
        for template_type in template_types:
            try:
                template = self.factory.create_template(template_type)
                if template:
                    self._templates[template_type] = template
            except Exception as e:
                self.error_handler.log_error(e, f"Failed to initialize template: {template_type}")
    
    def get_template(self, name: str) -> Optional[TemplateProtocol]:
        """テンプレートを取得"""
        return self._templates.get(name)
    
    def list_templates(self) -> List[str]:
        """利用可能なテンプレート一覧を取得"""
        return list(self._templates.keys())
    
    def generate_complete_workflow(
        self,
        template_name: str,
        input_text: str,
        output_dir: str,
        resolution=(1080, 1920),
        generate_video=True,
        **parameters
    ):
        """完全なワークフロー実行"""
        from .models.output_models import GenerationResult, ASSOutput, VideoOutput
        import os
        import time
        
        start_time = time.time()
        
        try:
            # テンプレート取得
            template = self.get_template(template_name)
            if not template:
                raise ValueError(f"Template '{template_name}' not found")
            
            # テキスト処理
            text_formatter = self.factory.create_text_formatter()
            formatted_text = text_formatter.format_for_display(input_text)
            
            # パラメータ設定
            template_params = self.config.get_template_settings(template_name)
            template_params.update(parameters)
            validated_params = template.validate_parameters(**template_params)
            
            # ASS生成
            ass_content = template.generate_ass_from_formatted(
                formatted_text, resolution, **validated_params
            )
            
            # ASS保存
            os.makedirs(output_dir, exist_ok=True)
            ass_path = os.path.join(output_dir, f"{template_name}_output.ass")
            
            with open(ass_path, 'w', encoding='utf-8') as f:
                f.write(ass_content)
            
            # メタデータを作成
            from .models.output_models import ASSMetadata
            metadata = ASSMetadata()
            metadata.line_count = len(ass_content.split('\n'))
            metadata.character_count = len(ass_content)
            
            ass_output = ASSOutput(
                content=ass_content,
                metadata=metadata
            )
            
            # 動画生成
            video_output = None
            total_duration = template.calculate_total_duration(formatted_text, **validated_params)
            
            if generate_video:
                video_generator = self.factory.create_video_generator(resolution)
                video_path = os.path.join(output_dir, f"{template_name}_output.mp4")
                
                success = video_generator.create_greenscreen_video(
                    ass_file_path=ass_path,
                    output_path=video_path,
                    duration=total_duration,
                    resolution=resolution
                )
                
                if success and os.path.exists(video_path):
                    video_output = VideoOutput(
                        file_path=video_path,
                        resolution=resolution,
                        duration=total_duration
                    )
            
            processing_time = time.time() - start_time
            
            return GenerationResult(
                success=True,
                ass_output=ass_output,
                video_output=video_output,
                template_name=template_name
            )
            
        except Exception as e:
            context = {
                'template_name': template_name,
                'input_text': input_text[:100] + '...' if len(input_text) > 100 else input_text,
                'output_dir': output_dir,
                'resolution': resolution,
                'parameters': parameters
            }
            return self.error_handler.handle_generation_error(e, context)


# グローバルコンテナインスタンス
_global_container: Optional[ServiceContainer] = None
_container_lock = threading.RLock()


def get_container() -> ServiceContainer:
    """グローバルサービスコンテナを取得"""
    global _global_container
    
    with _container_lock:
        if _global_container is None:
            _global_container = ServiceContainer()
            _configure_default_services(_global_container)
        
        return _global_container


def _configure_default_services(container: ServiceContainer):
    """デフォルトサービスを設定"""
    # 設定サービス
    config = Configuration()
    container.register_singleton(Configuration, config)
    
    # エラーハンドラー
    error_handler = ErrorHandler()
    container.register_singleton(ErrorHandler, error_handler)
    
    # サービスファクトリー
    factory = ServiceFactory(container)
    container.register_singleton(ServiceFactory, factory)
    
    # テンプレートエンジン
    template_engine = DependencyInjectedTemplateEngine(container)
    container.register_singleton(DependencyInjectedTemplateEngine, template_engine)


def reset_container():
    """グローバルコンテナをリセット（テスト用）"""
    global _global_container
    
    with _container_lock:
        if _global_container:
            _global_container.clear()
        _global_container = None