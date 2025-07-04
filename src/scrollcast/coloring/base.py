"""
Base Template (New Architecture)
ASS字幕生成に特化した基底クラス
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from ..boxing import FormattedText


@dataclass
class TemplateParameter:
    """テンプレートパラメータの定義"""
    name: str
    type: type
    default: Any
    description: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    choices: Optional[List[Any]] = None


@dataclass
class SubtitleTemplate:
    """字幕テンプレートの定義"""
    name: str
    description: str
    parameters: Dict[str, TemplateParameter] = field(default_factory=dict)


@dataclass
class TimingInfo:
    """タイミング情報"""
    start_time: float  # 秒
    end_time: float    # 秒
    layer: int = 0
    
    def get_ass_start_time(self) -> str:
        """ASS形式の開始時間を取得"""
        return self._format_ass_time(self.start_time)
    
    def get_ass_end_time(self) -> str:
        """ASS形式の終了時間を取得"""
        return self._format_ass_time(self.end_time)
    
    def _format_ass_time(self, seconds: float) -> str:
        """秒数をASS時間フォーマットに変換"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:05.2f}"


class BaseTemplate(ABC):
    """ASS字幕生成に特化した基底クラス"""
    
    def __init__(self):
        """初期化"""
        pass
    
    @property
    @abstractmethod
    def template_info(self) -> SubtitleTemplate:
        """テンプレート情報を返す"""
        pass
    
    @abstractmethod
    def generate_ass_from_formatted(self, formatted_text: FormattedText, **kwargs) -> str:
        """整形済みテキストからASS字幕を生成
        
        Args:
            formatted_text: 整形済みテキスト
            **kwargs: テンプレート固有のパラメータ
        
        Returns:
            完全なASS字幕内容
        """
        pass
    
    @abstractmethod
    def calculate_total_duration(self, formatted_text: FormattedText, **kwargs) -> float:
        """総再生時間を計算
        
        Args:
            formatted_text: 整形済みテキスト
            **kwargs: テンプレート固有のパラメータ
        
        Returns:
            総時間（秒）
        """
        pass
    
    def generate_ass_header(self, resolution: tuple = (1080, 1920), **kwargs) -> str:
        """ASSヘッダーを生成
        
        Args:
            resolution: 画面解像度 (width, height)
            **kwargs: 追加のヘッダーパラメータ
        
        Returns:
            ASSヘッダー文字列
        """
        width, height = resolution
        
        # スタイル設定の取得
        font_name = kwargs.get('font_name', 'Arial')
        font_size = kwargs.get('font_size', 64)
        primary_color = kwargs.get('primary_color', '&H00FFFFFF')  # 白
        outline_color = kwargs.get('outline_color', '&H00000000')  # 黒
        back_color = kwargs.get('back_color', '&H80000000')        # 半透明黒
        
        header = f"""[Script Info]
Title: {self.template_info.name.title()} Effect
ScriptType: v4.00+
WrapStyle: 2
PlayResX: {width}
PlayResY: {height}
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: {self.template_info.name.title()},{font_name},{font_size},{primary_color},&H000000FF,{outline_color},{back_color},1,0,0,0,100,100,0,0,1,3,0,5,60,60,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        return header
    
    def create_dialogue_line(self, text: str, timing: TimingInfo, 
                           style_name: Optional[str] = None) -> str:
        """Dialogue行を作成
        
        Args:
            text: 表示テキスト（ASS効果を含む）
            timing: タイミング情報
            style_name: スタイル名（Noneの場合はテンプレート名）
        
        Returns:
            Dialogue行文字列
        """
        if style_name is None:
            style_name = self.template_info.name.title()
        
        return (f"Dialogue: {timing.layer},"
                f"{timing.get_ass_start_time()},"
                f"{timing.get_ass_end_time()},"
                f"{style_name},,0,0,0,,{text}")
    
    def validate_parameters(self, **kwargs) -> Dict[str, Any]:
        """パラメータをバリデーションして有効な値を返す
        
        Args:
            **kwargs: 検証するパラメータ
        
        Returns:
            バリデーション済みパラメータ
        
        Raises:
            ValueError: 無効なパラメータ
        """
        # Pydanticパラメータクラスがある場合はそれを使用
        pydantic_params = self._validate_with_pydantic(**kwargs)
        if pydantic_params is not None:
            return pydantic_params
        
        # 従来のvalidation（後方互換性のため）
        return self._validate_with_legacy(**kwargs)
    
    def _validate_with_pydantic(self, **kwargs) -> Optional[Dict[str, Any]]:
        """Pydanticを使ったパラメータvalidation
        
        Args:
            **kwargs: 検証するパラメータ
        
        Returns:
            バリデーション済みパラメータ、または失敗時はNone
        """
        try:
            from .parameters import get_parameter_class
            param_class = get_parameter_class(self.template_info.name)
            if param_class is None:
                return None
            
            # Pydanticオブジェクトを作成し、辞書に変換
            param_obj = param_class(**kwargs)
            return param_obj.model_dump()
            
        except ImportError:
            # parametersモジュールが利用できない場合
            return None
        except Exception:
            # Pydantic validationが失敗した場合は例外を再発生
            raise
    
    def _validate_with_legacy(self, **kwargs) -> Dict[str, Any]:
        """従来のvalidation方式（後方互換性のため）"""
        validated = {}
        template_params = self.template_info.parameters
        
        # 共通パラメータ（全テンプレートで使用可能）
        common_params = {'font_size', 'resolution', 'font_name', 'primary_color', 
                        'outline_color', 'back_color'}
        
        for name, value in kwargs.items():
            # 共通パラメータの場合はそのまま通す
            if name in common_params:
                validated[name] = value
                continue
            
            # テンプレート固有パラメータの検証
            if name not in template_params:
                print(f"Warning: Unknown parameter '{name}' for template '{self.template_info.name}'")
                continue
            
            param = template_params[name]
            
            # 型チェック
            if not isinstance(value, param.type):
                try:
                    value = param.type(value)
                except (ValueError, TypeError):
                    raise ValueError(f"Parameter {name} must be of type {param.type.__name__}")
            
            # 範囲チェック
            if param.min_value is not None and value < param.min_value:
                raise ValueError(f"Parameter {name} must be >= {param.min_value}")
            
            if param.max_value is not None and value > param.max_value:
                raise ValueError(f"Parameter {name} must be <= {param.max_value}")
            
            # 選択肢チェック
            if param.choices is not None and value not in param.choices:
                raise ValueError(f"Parameter {name} must be one of {param.choices}")
            
            validated[name] = value
        
        # デフォルト値を設定
        for name, param in template_params.items():
            if name not in validated:
                validated[name] = param.default
        
        return validated
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """デフォルトパラメータを取得
        
        Returns:
            パラメータ名: デフォルト値の辞書
        """
        return {name: param.default for name, param in self.template_info.parameters.items()}
    
    def list_parameters(self) -> List[str]:
        """パラメータ名のリストを取得
        
        Returns:
            パラメータ名のリスト
        """
        return list(self.template_info.parameters.keys())
    
    def get_parameter_info(self, param_name: str) -> Optional[TemplateParameter]:
        """パラメータ情報を取得
        
        Args:
            param_name: パラメータ名
        
        Returns:
            パラメータ情報またはNone
        """
        return self.template_info.parameters.get(param_name)
    
    def process_text(self, text: str, font_size: int = 64, resolution: tuple = (1080, 1920)) -> FormattedText:
        """テキストを処理してFormattedTextを生成
        
        Args:
            text: 入力テキスト
            font_size: フォントサイズ
            resolution: 解像度
        
        Returns:
            処理済みテキスト
        """
        from ..boxing import DisplayConfig, TextFormatter
        
        config = DisplayConfig.create_mobile_portrait(font_size=font_size)
        formatter = TextFormatter(config)
        return formatter.format_for_display(text)
    
    def calculate_line_timings(self, formatted_text: FormattedText, 
                              base_duration: float, overlap_duration: float = 0.0) -> List[TimingInfo]:
        """行ごとのタイミングを計算
        
        Args:
            formatted_text: 整形済みテキスト
            base_duration: 基本表示時間（秒）
            overlap_duration: 重複時間（秒）
        
        Returns:
            各行のタイミング情報リスト
        """
        text_lines = formatted_text.get_text_lines()
        timings = []
        current_time = 0.0
        
        # 複雑さによる調整
        line_complexities = formatted_text.get_timing_hint('line_complexities', [1.0] * len(text_lines))
        reading_speed_multiplier = formatted_text.get_timing_hint('reading_speed_multiplier', 1.0)
        
        for i, line in enumerate(text_lines):
            if not line.strip():
                continue
            
            # 複雑さを考慮した表示時間
            complexity = line_complexities[i] if i < len(line_complexities) else 1.0
            duration = base_duration * complexity * reading_speed_multiplier
            
            timing = TimingInfo(
                start_time=current_time,
                end_time=current_time + duration,
                layer=0
            )
            timings.append(timing)
            
            # 次の行の開始時間（重複を考慮）
            current_time += duration - overlap_duration
        
        return timings
    
    def handle_empty_lines(self, formatted_text: FormattedText, 
                          empty_line_duration: float = 0.5) -> List[TimingInfo]:
        """空行用のタイミングを処理
        
        Args:
            formatted_text: 整形済みテキスト
            empty_line_duration: 空行の表示時間（秒）
        
        Returns:
            空行のタイミング情報リスト
        """
        empty_timings = []
        
        if not formatted_text.empty_line_positions:
            return empty_timings
        
        # 基本的な行タイミングを取得
        base_timings = self.calculate_line_timings(formatted_text, 2.0)  # 仮の基本時間
        
        for empty_pos in formatted_text.empty_line_positions:
            # 空行の前後の時間を推定
            if empty_pos > 0 and empty_pos - 1 < len(base_timings):
                prev_timing = base_timings[empty_pos - 1]
                start_time = prev_timing.end_time
            else:
                start_time = 0.0
            
            timing = TimingInfo(
                start_time=start_time,
                end_time=start_time + empty_line_duration,
                layer=1  # 空行は別レイヤー
            )
            empty_timings.append(timing)
        
        return empty_timings
    
    def apply_paragraph_spacing(self, timings: List[TimingInfo], 
                               formatted_text: FormattedText,
                               paragraph_gap: float = 1.0) -> List[TimingInfo]:
        """段落間スペースを適用
        
        Args:
            timings: 元のタイミングリスト
            formatted_text: 整形済みテキスト
            paragraph_gap: 段落間の追加時間（秒）
        
        Returns:
            調整されたタイミングリスト
        """
        if not formatted_text.paragraph_breaks:
            return timings
        
        adjusted_timings = []
        time_offset = 0.0
        
        for i, timing in enumerate(timings):
            # 段落区切りの後の行かチェック
            is_after_paragraph_break = any(
                break_pos < i for break_pos in formatted_text.paragraph_breaks
            )
            
            if is_after_paragraph_break and i > 0:
                time_offset += paragraph_gap
            
            adjusted_timing = TimingInfo(
                start_time=timing.start_time + time_offset,
                end_time=timing.end_time + time_offset,
                layer=timing.layer
            )
            adjusted_timings.append(adjusted_timing)
        
        return adjusted_timings
    
    def calculate_duration(self, formatted_text: FormattedText, **kwargs) -> float:
        """総時間を計算
        
        Args:
            formatted_text: 整形済みテキスト
            **kwargs: テンプレート固有のパラメータ
        
        Returns:
            総時間（秒）
        """
        # calculate_total_durationが実装されている場合はそれを使用
        if hasattr(self, 'calculate_total_duration') and callable(getattr(self, 'calculate_total_duration')):
            return self.calculate_total_duration(formatted_text, **kwargs)
        
        # デフォルト実装：各行2秒 + 段落間1秒
        text_lines = len(formatted_text.get_text_lines())
        paragraph_breaks = len(formatted_text.paragraph_breaks)
        
        return text_lines * 2.0 + paragraph_breaks * 1.0
    
    def generate_ass_effects(self, processed_text: FormattedText, **kwargs) -> str:
        """ASS効果を生成（デフォルト実装）
        
        Args:
            processed_text: 処理済みテキスト
            **kwargs: テンプレート固有のパラメータ
        
        Returns:
            ASS効果文字列
        """
        # デフォルト実装では完全なASSファイルを生成
        return self.generate_ass_from_formatted(processed_text, **kwargs)