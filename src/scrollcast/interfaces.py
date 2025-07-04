"""
Dependency Injection Interfaces
依存性注入用のProtocol定義
"""

from typing import Protocol, Optional, Any, Dict, List, Tuple, Union
from abc import ABC, abstractmethod

from .models.display_models import DisplayConfig, Resolution
from .models.text_models import FormattedText, TextContent
from .models.effect_models import EffectParams, TimingInfo
from .models.output_models import ASSOutput, VideoOutput, GenerationResult


# Boxing Layer Protocols

class TextFormatterProtocol(Protocol):
    """テキスト構造化・改行処理層のプロトコル"""
    
    def format_for_display(
        self, 
        text: str, 
        config: Optional[DisplayConfig] = None
    ) -> FormattedText:
        """テキストを表示用に整形"""
        ...


class DisplayConfigProtocol(Protocol):
    """表示設定プロトコル"""
    
    @classmethod
    def create_mobile_portrait(
        cls, 
        font_size: int = 64,
        resolution: Optional[Resolution] = None
    ) -> DisplayConfig:
        """モバイル縦向け設定を作成"""
        ...


# Coloring Layer Protocols

class TemplateProtocol(Protocol):
    """テンプレート層のプロトコル"""
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """デフォルトパラメータを取得"""
        ...
    
    def validate_parameters(self, **params: Any) -> Dict[str, Any]:
        """パラメータをバリデーション"""
        ...
    
    def generate_ass_from_formatted(
        self, 
        formatted: FormattedText, 
        resolution: Tuple[int, int] = (1080, 1920),
        **params: Any
    ) -> str:
        """整形済みテキストからASS生成"""
        ...
    
    def calculate_total_duration(
        self, 
        formatted: FormattedText, 
        **params: Any
    ) -> float:
        """総時間を計算"""
        ...


# Packing Layer Protocols

class ASSBuilderProtocol(Protocol):
    """ASS構築層のプロトコル"""
    
    def add_style(
        self, 
        name: str, 
        font_size: int = 64,
        font_name: str = "Arial",
        **style_params: Any
    ) -> None:
        """スタイルを追加"""
        ...
    
    def add_dialogue(
        self,
        start_time: str,
        end_time: str,
        style: str,
        text: str,
        **dialogue_params: Any
    ) -> None:
        """ダイアログを追加"""
        ...
    
    def build(self) -> str:
        """ASSコンテンツを構築"""
        ...


# Rendering Layer Protocols

class VideoGeneratorProtocol(Protocol):
    """動画生成層のプロトコル"""
    
    def create_video_with_subtitles(
        self,
        ass_file_path: str,
        output_path: str,
        duration: float,
        resolution: Optional[Tuple[int, int]] = None,
        background_color: str = "black",
        fps: int = 30,
        quality_preset: str = "fast",
        crf: int = 23
    ) -> bool:
        """字幕付き動画を生成"""
        ...
    
    def create_greenscreen_video(
        self,
        ass_file_path: str,
        output_path: str,
        duration: float,
        resolution: Optional[Tuple[int, int]] = None
    ) -> bool:
        """グリーンスクリーン動画を生成"""
        ...


# Orchestrator Layer Protocols

class TemplateEngineProtocol(Protocol):
    """テンプレートエンジン層のプロトコル"""
    
    def register_template(self, template: TemplateProtocol) -> None:
        """テンプレートを登録"""
        ...
    
    def get_template(self, name: str) -> Optional[TemplateProtocol]:
        """テンプレートを取得"""
        ...
    
    def list_templates(self) -> List[str]:
        """利用可能なテンプレート一覧を取得"""
        ...
    
    def generate_subtitle(
        self,
        template_name: str,
        text: Union[str, List[str]],
        output_path: str,
        resolution: Tuple[int, int] = (1080, 1920),
        **parameters: Any
    ) -> bool:
        """字幕を生成"""
        ...
    
    def generate_video(
        self,
        template_name: str,
        text: Union[str, List[str]],
        output_path: str,
        ass_path: Optional[str] = None,
        resolution: Tuple[int, int] = (1080, 1920),
        **parameters: Any
    ) -> bool:
        """動画を生成"""
        ...


# Service Container Protocol

class ServiceContainerProtocol(Protocol):
    """サービスコンテナのプロトコル"""
    
    def register(self, service_type: type, implementation: Any) -> None:
        """サービスを登録"""
        ...
    
    def get(self, service_type: type) -> Any:
        """サービスを取得"""
        ...
    
    def create_template_engine(self) -> TemplateEngineProtocol:
        """テンプレートエンジンを作成"""
        ...


# Abstract Base Classes for Dependency Injection

class AbstractService(ABC):
    """サービス基底クラス"""
    pass


class AbstractTemplateEngine(AbstractService):
    """テンプレートエンジン抽象基底クラス"""
    
    @abstractmethod
    def generate_complete_workflow(
        self,
        template_name: str,
        input_text: str,
        output_dir: str,
        resolution: Tuple[int, int] = (1080, 1920),
        **parameters: Any
    ) -> GenerationResult:
        """完全なワークフロー実行"""
        pass


class AbstractVideoService(AbstractService):
    """動画サービス抽象基底クラス"""
    
    @abstractmethod
    def generate_video_from_text(
        self,
        text: str,
        template_name: str,
        output_path: str,
        **options: Any
    ) -> VideoOutput:
        """テキストから動画を生成"""
        pass


# Factory Protocols

class TemplateFactoryProtocol(Protocol):
    """テンプレートファクトリのプロトコル"""
    
    def create_template(self, template_type: str) -> TemplateProtocol:
        """テンプレートを作成"""
        ...
    
    def get_available_templates(self) -> List[str]:
        """利用可能なテンプレート一覧を取得"""
        ...


class ServiceFactoryProtocol(Protocol):
    """サービスファクトリのプロトコル"""
    
    def create_text_formatter(self, config: DisplayConfig) -> TextFormatterProtocol:
        """テキストフォーマッターを作成"""
        ...
    
    def create_video_generator(
        self, 
        resolution: Tuple[int, int] = (1080, 1920)
    ) -> VideoGeneratorProtocol:
        """動画ジェネレーターを作成"""
        ...
    
    def create_ass_builder(self, title: str = "Subtitle") -> ASSBuilderProtocol:
        """ASSビルダーを作成"""
        ...


# Error Handling Protocols

class ErrorHandlerProtocol(Protocol):
    """エラーハンドラーのプロトコル"""
    
    def handle_generation_error(
        self, 
        error: Exception, 
        context: Dict[str, Any]
    ) -> GenerationResult:
        """生成エラーを処理"""
        ...
    
    def log_error(self, error: Exception, details: str) -> None:
        """エラーをログ出力"""
        ...


# Configuration Protocols

class ConfigurationProtocol(Protocol):
    """設定管理のプロトコル"""
    
    def get_default_resolution(self) -> Tuple[int, int]:
        """デフォルト解像度を取得"""
        ...
    
    def get_quality_settings(self) -> Dict[str, Any]:
        """品質設定を取得"""
        ...
    
    def get_template_settings(self, template_name: str) -> Dict[str, Any]:
        """テンプレート設定を取得"""
        ...