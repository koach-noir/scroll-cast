"""
Parameter Models using Pydantic
Pydanticベースのパラメータモデル定義
"""

from typing import Union, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


class ParameterBase(BaseModel):
    """全パラメータの基底クラス"""
    
    model_config = ConfigDict(
        # 追加フィールドを許可（後方互換性のため）
        extra='allow',
        # フィールド名のバリデーション有効化
        validate_assignment=True,
        # JSON スキーマ生成時の説明を含める
        json_schema_extra={}
    )


class TimingParametersMixin(ParameterBase):
    """共通のタイミングパラメータ"""
    
    fade_duration: float = Field(
        default=0.1,
        ge=0.05, 
        le=0.5,
        description="各要素のフェード時間（秒）"
    )
    
    pause_duration: float = Field(
        default=1.0,
        ge=0.0,
        le=3.0,
        description="要素間の一時停止時間（秒）"
    )


class AnimationParametersMixin(ParameterBase):
    """共通のアニメーションパラメータ"""
    
    animation_duration: float = Field(
        default=8.0,
        ge=1.0,
        le=20.0,
        description="アニメーション総時間（秒）"
    )


class FontParametersMixin(ParameterBase):
    """共通のフォントパラメータ"""
    
    font_size: int = Field(
        default=36,
        ge=12,
        le=144,
        description="フォントサイズ（ピクセル）"
    )
    
    font_name: str = Field(
        default="Arial",
        description="フォント名"
    )


class TypewriterParameters(TimingParametersMixin, FontParametersMixin):
    """タイプライター効果専用パラメータ"""
    
    char_interval: float = Field(
        default=0.15,
        ge=0.05,
        le=1.0,
        description="文字表示間隔（秒）"
    )
    
    pause_between_lines: float = Field(
        default=1.0,
        ge=0.0,
        le=3.0,
        description="行間の間隔（秒）"
    )
    
    pause_between_paragraphs: float = Field(
        default=2.0,
        ge=0.0,
        le=5.0,
        description="段落間の間隔（秒）"
    )
    
    @field_validator('char_interval')
    @classmethod
    def validate_char_interval(cls, v, info):
        """文字間隔がフェード時間より長いことを確認"""
        if info.data and 'fade_duration' in info.data and v < info.data['fade_duration']:
            raise ValueError('char_interval must be >= fade_duration')
        return v


class RailwayScrollParameters(TimingParametersMixin, FontParametersMixin):
    """鉄道方向幕スクロール効果専用パラメータ"""
    
    fade_in_duration: float = Field(
        default=0.8,
        ge=0.2,
        le=2.0,
        description="フェードイン時間（秒）"
    )
    
    pause_duration: float = Field(
        default=2.0,
        ge=0.5,
        le=5.0,
        description="中央での一時停止時間（秒）"
    )
    
    fade_out_duration: float = Field(
        default=0.8,
        ge=0.2,
        le=2.0,
        description="フェードアウト時間（秒）"
    )
    
    overlap_duration: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="次行との重複時間（秒）"
    )
    
    empty_line_pause: float = Field(
        default=1.0,
        ge=0.0,
        le=3.0,
        description="空行での一時停止時間（秒）"
    )


class SimpleRoleParameters(AnimationParametersMixin, FontParametersMixin):
    """シンプルロール効果専用パラメータ"""
    
    line_interval: float = Field(
        default=0.2,
        ge=0.1,
        le=2.0,
        description="行間間隔時間（秒）"
    )
    
    scroll_speed: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="スクロール速度倍率"
    )


class HorizontalTickerParameters(FontParametersMixin):
    """水平ティッカー効果専用パラメータ"""
    
    scroll_speed: float = Field(
        default=1.0,
        ge=0.3,
        le=3.0,
        description="スクロール速度倍率"
    )
    
    text_spacing: float = Field(
        default=2.0,
        ge=1.0,
        le=5.0,
        description="テキスト区切り間隔（画面幅倍率）"
    )
    
    loop_behavior: str = Field(
        default="continuous",
        description="ループ動作（continuous/stop）"
    )
    
    fade_edges: bool = Field(
        default=True,
        description="画面端でのフェード効果"
    )
    
    ticker_duration: float = Field(
        default=10.0,
        ge=5.0,
        le=30.0,
        description="1回の横断時間（秒）"
    )
    
    @field_validator('loop_behavior')
    @classmethod
    def validate_loop_behavior(cls, v):
        """ループ動作の値を検証"""
        allowed = ["continuous", "stop"]
        if v not in allowed:
            raise ValueError(f'loop_behavior must be one of {allowed}')
        return v


# テンプレート名とパラメータクラスのマッピング
PARAMETER_CLASSES = {
    'typewriter_fade': TypewriterParameters,
    'railway_scroll': RailwayScrollParameters,
    'simple_role': SimpleRoleParameters,
    'horizontal_ticker': HorizontalTickerParameters,
}


def get_parameter_class(template_name: str) -> Optional[type]:
    """テンプレート名からパラメータクラスを取得
    
    Args:
        template_name: テンプレート名
        
    Returns:
        対応するパラメータクラス、見つからない場合はNone
    """
    return PARAMETER_CLASSES.get(template_name)


def create_parameters(template_name: str, **kwargs) -> Optional[ParameterBase]:
    """テンプレート名とキーワード引数からパラメータオブジェクトを作成
    
    Args:
        template_name: テンプレート名
        **kwargs: パラメータ値
        
    Returns:
        パラメータオブジェクト、テンプレートが見つからない場合はNone
    """
    parameter_class = get_parameter_class(template_name)
    if parameter_class is None:
        return None
    
    return parameter_class(**kwargs)


def validate_parameters(template_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """パラメータを検証し、検証済み辞書を返す
    
    Args:
        template_name: テンプレート名
        parameters: 検証するパラメータ辞書
        
    Returns:
        検証済みパラメータ辞書
        
    Raises:
        ValueError: パラメータが無効な場合
    """
    param_obj = create_parameters(template_name, **parameters)
    if param_obj is None:
        raise ValueError(f"Unknown template: {template_name}")
    
    return param_obj.model_dump()