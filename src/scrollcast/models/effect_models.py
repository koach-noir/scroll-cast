"""
Effect Models
エフェクト・タイミング関連のデータモデル
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union, Tuple
from enum import Enum
import math


class EasingType(Enum):
    """イージングタイプ"""
    LINEAR = "linear"
    EASE_IN = "ease-in"
    EASE_OUT = "ease-out"
    EASE_IN_OUT = "ease-in-out"
    ELASTIC = "elastic"
    BOUNCE = "bounce"
    CUSTOM = "custom"


class AnimationDirection(Enum):
    """アニメーション方向"""
    LEFT_TO_RIGHT = "left-to-right"
    RIGHT_TO_LEFT = "right-to-left"
    TOP_TO_BOTTOM = "top-to-bottom"
    BOTTOM_TO_TOP = "bottom-to-top"
    CENTER_OUT = "center-out"
    RANDOM = "random"


class EffectPreset(Enum):
    """エフェクトプリセット"""
    SMOOTH_TYPEWRITER = "smooth_typewriter"
    FAST_TYPEWRITER = "fast_typewriter"
    SLOW_FADE = "slow_fade"
    QUICK_SCROLL = "quick_scroll"
    SMOOTH_SCROLL = "smooth_scroll"
    DRAMATIC_FADE = "dramatic_fade"
    CUSTOM = "custom"


@dataclass
class TimingInfo:
    """タイミング情報の拡張版"""
    start_time: float  # 秒
    end_time: float    # 秒
    layer: int = 0
    
    # 拡張プロパティ
    fade_in_duration: float = 0.0    # フェードイン時間
    fade_out_duration: float = 0.0   # フェードアウト時間
    hold_duration: float = 0.0       # 表示保持時間
    
    # 位置・変形情報
    start_position: Optional[Tuple[float, float]] = None  # (x, y)
    end_position: Optional[Tuple[float, float]] = None
    start_scale: float = 1.0
    end_scale: float = 1.0
    start_rotation: float = 0.0
    end_rotation: float = 0.0
    start_alpha: float = 1.0
    end_alpha: float = 1.0
    
    # メタデータ
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初期化後の処理"""
        if self.hold_duration == 0.0:
            self.hold_duration = max(0.0, self.duration - self.fade_in_duration - self.fade_out_duration)
    
    @property
    def duration(self) -> float:
        """総時間を取得"""
        return self.end_time - self.start_time
    
    @duration.setter
    def duration(self, value: float) -> None:
        """総時間を設定"""
        self.end_time = self.start_time + value
    
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
    
    def get_fade_in_end_time(self) -> float:
        """フェードイン終了時間"""
        return self.start_time + self.fade_in_duration
    
    def get_fade_out_start_time(self) -> float:
        """フェードアウト開始時間"""
        return self.end_time - self.fade_out_duration
    
    def get_hold_start_time(self) -> float:
        """表示保持開始時間"""
        return self.get_fade_in_end_time()
    
    def get_hold_end_time(self) -> float:
        """表示保持終了時間"""
        return self.get_fade_out_start_time()
    
    def overlaps_with(self, other: 'TimingInfo') -> bool:
        """他のタイミングと重複するかチェック"""
        return not (self.end_time <= other.start_time or other.end_time <= self.start_time)
    
    def get_overlap_duration(self, other: 'TimingInfo') -> float:
        """重複時間を取得"""
        if not self.overlaps_with(other):
            return 0.0
        start = max(self.start_time, other.start_time)
        end = min(self.end_time, other.end_time)
        return max(0.0, end - start)
    
    @classmethod
    def create_with_duration(cls, start_time: float, duration: float, **kwargs) -> 'TimingInfo':
        """時間長指定で作成"""
        return cls(
            start_time=start_time,
            end_time=start_time + duration,
            **kwargs
        )
    
    @classmethod
    def create_simple(cls, start_time: float, end_time: float, layer: int = 0) -> 'TimingInfo':
        """シンプルなタイミング情報を作成（既存互換性）"""
        return cls(start_time=start_time, end_time=end_time, layer=layer)


@dataclass
class AnimationParams:
    """アニメーションパラメータ"""
    # 基本パラメータ
    char_interval: float = 0.1           # 文字間隔（秒）
    line_interval: float = 1.0           # 行間隔（秒）
    paragraph_interval: float = 2.0      # 段落間隔（秒）
    
    # エフェクト制御
    speed_multiplier: float = 1.0        # 速度倍率
    easing: EasingType = EasingType.EASE_OUT
    direction: AnimationDirection = AnimationDirection.LEFT_TO_RIGHT
    
    # フェード設定
    fade_in_duration: float = 0.0        # フェードイン時間
    fade_out_duration: float = 0.0       # フェードアウト時間
    fade_overlap: float = 0.0            # フェード重複時間
    
    # 動作設定
    stagger_delay: float = 0.0           # 要素間の遅延
    randomness: float = 0.0              # ランダム性（0-1）
    
    # 物理効果
    bounce_intensity: float = 0.0        # バウンス強度
    elastic_tension: float = 1.0         # 弾性張力
    
    # カスタムパラメータ
    custom_params: Dict[str, Any] = field(default_factory=dict)
    
    def apply_speed_multiplier(self, multiplier: float) -> 'AnimationParams':
        """速度倍率を適用した新しいインスタンスを返す"""
        return AnimationParams(
            char_interval=self.char_interval / multiplier,
            line_interval=self.line_interval / multiplier,
            paragraph_interval=self.paragraph_interval / multiplier,
            speed_multiplier=self.speed_multiplier * multiplier,
            easing=self.easing,
            direction=self.direction,
            fade_in_duration=self.fade_in_duration,
            fade_out_duration=self.fade_out_duration,
            fade_overlap=self.fade_overlap,
            stagger_delay=self.stagger_delay / multiplier,
            randomness=self.randomness,
            bounce_intensity=self.bounce_intensity,
            elastic_tension=self.elastic_tension,
            custom_params=self.custom_params.copy()
        )
    
    def get_randomized_interval(self, base_interval: float) -> float:
        """ランダム性を適用した間隔を取得"""
        if self.randomness <= 0:
            return base_interval
        
        import random
        variation = base_interval * self.randomness * 0.5
        return base_interval + random.uniform(-variation, variation)


@dataclass
class VisualParams:
    """視覚エフェクトパラメータ"""
    # 色設定
    primary_color: str = "&H00FFFFFF"     # プライマリ色
    secondary_color: str = "&H000000FF"   # セカンダリ色
    outline_color: str = "&H00000000"     # アウトライン色
    shadow_color: str = "&H80000000"      # 影色
    
    # アウトライン・影設定
    outline_width: int = 3               # アウトライン幅
    shadow_offset: int = 0               # 影のオフセット
    
    # 透明度設定
    alpha_start: float = 0.0             # 開始時透明度（0-1）
    alpha_end: float = 1.0               # 終了時透明度（0-1）
    
    # ブラー・歪み
    blur_radius: float = 0.0             # ブラー半径
    distortion: float = 0.0              # 歪み強度
    
    # グラデーション
    gradient_enabled: bool = False        # グラデーション有効
    gradient_start_color: str = ""        # グラデーション開始色
    gradient_end_color: str = ""          # グラデーション終了色
    gradient_direction: float = 0.0       # グラデーション方向（度）
    
    # カスタムASS効果
    custom_ass_effects: List[str] = field(default_factory=list)
    
    def to_ass_style_params(self) -> Dict[str, Any]:
        """ASSスタイル用パラメータに変換"""
        return {
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'outline_color': self.outline_color,
            'back_color': self.shadow_color,
            'outline': self.outline_width,
            'shadow': self.shadow_offset,
        }
    
    def get_alpha_at_progress(self, progress: float) -> float:
        """進行度に応じた透明度を取得"""
        progress = max(0.0, min(1.0, progress))
        return self.alpha_start + (self.alpha_end - self.alpha_start) * progress
    
    def generate_ass_color_effects(self, progress: float = 1.0) -> str:
        """ASS色エフェクトコードを生成"""
        effects = []
        
        # 透明度制御
        if self.alpha_start != 1.0 or self.alpha_end != 1.0:
            alpha = self.get_alpha_at_progress(progress)
            alpha_value = int(255 * (1.0 - alpha))
            effects.append(f"\\alpha&H{alpha_value:02X}&")
        
        # ブラー効果
        if self.blur_radius > 0:
            effects.append(f"\\blur{self.blur_radius}")
        
        # カスタム効果
        effects.extend(self.custom_ass_effects)
        
        return "".join(effects)


@dataclass
class EffectParams:
    """エフェクトパラメータの統一管理"""
    # 基本設定
    name: str = "default"
    description: str = ""
    preset: EffectPreset = EffectPreset.CUSTOM
    
    # コンポーネント
    animation: AnimationParams = field(default_factory=AnimationParams)
    visual: VisualParams = field(default_factory=VisualParams)
    
    # 全体制御
    enabled: bool = True
    priority: int = 0
    
    # 条件設定
    min_duration: float = 0.0            # 最小持続時間
    max_duration: float = 60.0           # 最大持続時間
    
    # 品質・パフォーマンス
    quality_level: int = 5               # 品質レベル（1-10）
    optimization_enabled: bool = True     # 最適化有効
    
    # メタデータ
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        """パラメータ検証"""
        errors = []
        
        if not self.name:
            errors.append("Effect name is required")
        
        if self.animation.char_interval < 0:
            errors.append("Character interval must be >= 0")
        
        if self.min_duration < 0:
            errors.append("Minimum duration must be >= 0")
        
        if self.max_duration <= self.min_duration:
            errors.append("Maximum duration must be > minimum duration")
        
        if not (1 <= self.quality_level <= 10):
            errors.append("Quality level must be between 1 and 10")
        
        return errors
    
    def is_valid(self) -> bool:
        """有効なパラメータかチェック"""
        return len(self.validate()) == 0
    
    def apply_preset(self, preset: EffectPreset) -> 'EffectParams':
        """プリセットを適用した新しいインスタンスを返す"""
        new_params = EffectParams(
            name=self.name,
            description=self.description,
            preset=preset,
            enabled=self.enabled,
            priority=self.priority,
            min_duration=self.min_duration,
            max_duration=self.max_duration,
            quality_level=self.quality_level,
            optimization_enabled=self.optimization_enabled,
            metadata=self.metadata.copy()
        )
        
        # プリセット別設定
        if preset == EffectPreset.SMOOTH_TYPEWRITER:
            new_params.animation = AnimationParams(
                char_interval=0.1,
                line_interval=1.0,
                fade_in_duration=0.2,
                easing=EasingType.EASE_OUT
            )
        elif preset == EffectPreset.FAST_TYPEWRITER:
            new_params.animation = AnimationParams(
                char_interval=0.05,
                line_interval=0.5,
                fade_in_duration=0.1,
                easing=EasingType.LINEAR
            )
        elif preset == EffectPreset.SLOW_FADE:
            new_params.animation = AnimationParams(
                char_interval=0.2,
                line_interval=2.0,
                fade_in_duration=0.5,
                fade_out_duration=0.5,
                easing=EasingType.EASE_IN_OUT
            )
        elif preset == EffectPreset.QUICK_SCROLL:
            new_params.animation = AnimationParams(
                char_interval=0.02,
                line_interval=0.3,
                direction=AnimationDirection.TOP_TO_BOTTOM,
                easing=EasingType.EASE_OUT
            )
        elif preset == EffectPreset.SMOOTH_SCROLL:
            new_params.animation = AnimationParams(
                char_interval=0.05,
                line_interval=0.8,
                direction=AnimationDirection.TOP_TO_BOTTOM,
                easing=EasingType.EASE_IN_OUT
            )
        elif preset == EffectPreset.DRAMATIC_FADE:
            new_params.animation = AnimationParams(
                char_interval=0.15,
                line_interval=1.5,
                fade_in_duration=0.8,
                fade_out_duration=0.8,
                easing=EasingType.ELASTIC
            )
            new_params.visual = VisualParams(
                alpha_start=0.0,
                alpha_end=1.0,
                outline_width=4
            )
        
        return new_params
    
    def merge_with(self, other: 'EffectParams') -> 'EffectParams':
        """他のパラメータとマージ"""
        merged = EffectParams(
            name=other.name or self.name,
            description=other.description or self.description,
            preset=other.preset if other.preset != EffectPreset.CUSTOM else self.preset,
            enabled=other.enabled if hasattr(other, 'enabled') else self.enabled,
            priority=max(self.priority, other.priority),
            min_duration=max(self.min_duration, other.min_duration),
            max_duration=min(self.max_duration, other.max_duration),
            quality_level=other.quality_level if other.quality_level != 5 else self.quality_level,
            optimization_enabled=self.optimization_enabled and other.optimization_enabled,
            metadata={**self.metadata, **other.metadata}
        )
        
        # アニメーションパラメータのマージ
        merged.animation = AnimationParams(
            char_interval=other.animation.char_interval if other.animation.char_interval != 0.1 else self.animation.char_interval,
            line_interval=other.animation.line_interval if other.animation.line_interval != 1.0 else self.animation.line_interval,
            paragraph_interval=other.animation.paragraph_interval if other.animation.paragraph_interval != 2.0 else self.animation.paragraph_interval,
            speed_multiplier=other.animation.speed_multiplier * self.animation.speed_multiplier,
            easing=other.animation.easing if other.animation.easing != EasingType.EASE_OUT else self.animation.easing,
            direction=other.animation.direction if other.animation.direction != AnimationDirection.LEFT_TO_RIGHT else self.animation.direction,
            fade_in_duration=other.animation.fade_in_duration if other.animation.fade_in_duration != 0.0 else self.animation.fade_in_duration,
            fade_out_duration=other.animation.fade_out_duration if other.animation.fade_out_duration != 0.0 else self.animation.fade_out_duration,
            custom_params={**self.animation.custom_params, **other.animation.custom_params}
        )
        
        return merged


@dataclass
class EffectConfig:
    """エフェクト設定の最上位管理クラス"""
    # 基本情報
    name: str = "default_config"
    version: str = "1.0.0"
    description: str = ""
    
    # エフェクトパラメータ
    effects: List[EffectParams] = field(default_factory=list)
    
    # グローバル設定
    global_speed_multiplier: float = 1.0
    global_quality_level: int = 5
    
    # 最適化設定
    enable_gpu_acceleration: bool = False
    enable_multithreading: bool = True
    cache_enabled: bool = True
    
    # デバッグ・ログ
    debug_mode: bool = False
    log_level: str = "INFO"
    
    # メタデータ
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_effect(self, effect: EffectParams) -> None:
        """エフェクトを追加"""
        self.effects.append(effect)
    
    def get_effect_by_name(self, name: str) -> Optional[EffectParams]:
        """名前でエフェクトを取得"""
        for effect in self.effects:
            if effect.name == name:
                return effect
        return None
    
    def remove_effect(self, name: str) -> bool:
        """エフェクトを削除"""
        for i, effect in enumerate(self.effects):
            if effect.name == name:
                del self.effects[i]
                return True
        return False
    
    def get_primary_effect(self) -> Optional[EffectParams]:
        """プライマリエフェクトを取得"""
        if not self.effects:
            return None
        return max(self.effects, key=lambda e: e.priority)
    
    def validate_all(self) -> Dict[str, List[str]]:
        """全エフェクトを検証"""
        validation_results = {}
        for effect in self.effects:
            errors = effect.validate()
            if errors:
                validation_results[effect.name] = errors
        return validation_results
    
    def is_valid(self) -> bool:
        """設定全体が有効かチェック"""
        return len(self.validate_all()) == 0
    
    def optimize_for_performance(self) -> 'EffectConfig':
        """パフォーマンス最適化された設定を返す"""
        optimized = EffectConfig(
            name=f"{self.name}_optimized",
            version=self.version,
            description=f"Optimized version of {self.description}",
            global_speed_multiplier=self.global_speed_multiplier,
            global_quality_level=max(1, self.global_quality_level - 2),
            enable_gpu_acceleration=True,
            enable_multithreading=True,
            cache_enabled=True,
            debug_mode=False,
            log_level="WARN",
            metadata=self.metadata.copy()
        )
        
        for effect in self.effects:
            optimized_effect = EffectParams(
                name=effect.name,
                description=effect.description,
                preset=effect.preset,
                animation=effect.animation.apply_speed_multiplier(1.2),
                visual=effect.visual,
                enabled=effect.enabled,
                priority=effect.priority,
                quality_level=max(1, effect.quality_level - 1),
                optimization_enabled=True,
                metadata=effect.metadata.copy()
            )
            optimized.add_effect(optimized_effect)
        
        return optimized
    
    @classmethod
    def create_preset(cls, preset: EffectPreset, name: str = None) -> 'EffectConfig':
        """プリセットから設定を作成"""
        config_name = name or f"{preset.value}_config"
        
        config = cls(
            name=config_name,
            description=f"Preset configuration for {preset.value}"
        )
        
        effect_params = EffectParams(name=preset.value).apply_preset(preset)
        config.add_effect(effect_params)
        
        return config
    
    @classmethod
    def create_from_legacy_params(cls, **kwargs) -> 'EffectConfig':
        """既存パラメータから設定を作成（互換性）"""
        config = cls(name="legacy_config")
        
        # 既存パラメータの変換
        animation = AnimationParams(
            char_interval=kwargs.get('char_interval', 0.1),
            line_interval=kwargs.get('pause_between_lines', 1.0),
            paragraph_interval=kwargs.get('pause_between_paragraphs', 2.0),
            fade_in_duration=kwargs.get('fade_duration', 0.0),
        )
        
        visual = VisualParams(
            primary_color=kwargs.get('primary_color', '&H00FFFFFF'),
            outline_color=kwargs.get('outline_color', '&H00000000'),
            outline_width=kwargs.get('outline_width', 3),
        )
        
        effect = EffectParams(
            name="legacy_effect",
            animation=animation,
            visual=visual
        )
        
        config.add_effect(effect)
        return config


# 便利な関数群

def create_timing_sequence(base_time: float, intervals: List[float], 
                          durations: List[float], layer: int = 0) -> List[TimingInfo]:
    """タイミングシーケンスを作成"""
    timings = []
    current_time = base_time
    
    for i, (interval, duration) in enumerate(zip(intervals, durations)):
        timing = TimingInfo.create_with_duration(
            start_time=current_time,
            duration=duration,
            layer=layer
        )
        timings.append(timing)
        current_time += interval
    
    return timings


def calculate_optimal_intervals(text_length: int, total_duration: float, 
                               effect_params: EffectParams) -> List[float]:
    """最適な表示間隔を計算"""
    if text_length <= 0:
        return []
    
    base_interval = effect_params.animation.char_interval
    speed_factor = effect_params.animation.speed_multiplier
    
    # 総時間に合わせて調整
    target_total = total_duration / speed_factor
    actual_total = base_interval * text_length
    
    if actual_total > 0:
        adjustment = target_total / actual_total
        adjusted_interval = base_interval * adjustment
    else:
        adjusted_interval = base_interval
    
    # ランダム性の適用
    intervals = []
    for _ in range(text_length):
        interval = effect_params.animation.get_randomized_interval(adjusted_interval)
        intervals.append(max(0.001, interval))  # 最小間隔保証
    
    return intervals


def merge_timing_info(timings: List[TimingInfo], overlap_threshold: float = 0.1) -> List[TimingInfo]:
    """重複するタイミング情報をマージ"""
    if not timings:
        return []
    
    # 開始時間でソート
    sorted_timings = sorted(timings, key=lambda t: t.start_time)
    merged = [sorted_timings[0]]
    
    for current in sorted_timings[1:]:
        last_merged = merged[-1]
        
        # 重複チェック
        if current.start_time <= last_merged.end_time + overlap_threshold:
            # マージ
            last_merged.end_time = max(last_merged.end_time, current.end_time)
            last_merged.layer = min(last_merged.layer, current.layer)
        else:
            merged.append(current)
    
    return merged