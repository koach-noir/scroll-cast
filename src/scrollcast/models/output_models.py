"""
Output Models
出力・結果管理関連のデータモデル
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union, Tuple
from enum import Enum
from datetime import datetime
import os
import hashlib


class OutputFormat(Enum):
    """出力フォーマット"""
    ASS = "ass"
    SRT = "srt"
    VTT = "vtt"
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"


class ValidationLevel(Enum):
    """検証レベル"""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    CUSTOM = "custom"


class EncodingType(Enum):
    """エンコーディングタイプ"""
    UTF8 = "utf-8"
    UTF8_BOM = "utf-8-sig"
    UTF16 = "utf-16"
    SHIFT_JIS = "shift-jis"
    EUC_JP = "euc-jp"


class CompressionLevel(Enum):
    """圧縮レベル"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"


@dataclass
class ValidationResult:
    """検証結果"""
    is_valid: bool = True
    quality_score: float = 0.0  # 0-100の品質スコア
    
    # 検証項目別結果
    syntax_valid: bool = True
    timing_valid: bool = True
    encoding_valid: bool = True
    content_valid: bool = True
    
    # 警告・エラー
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    # 詳細メトリクス
    total_duration: float = 0.0
    line_count: int = 0
    character_count: int = 0
    average_line_duration: float = 0.0
    
    # 品質指標
    readability_score: float = 0.0      # 読みやすさ
    timing_accuracy: float = 0.0        # タイミング精度
    formatting_consistency: float = 0.0  # フォーマット一貫性
    
    # メタデータ
    validation_time: datetime = field(default_factory=datetime.now)
    validator_version: str = "1.0.0"
    
    def add_warning(self, message: str) -> None:
        """警告を追加"""
        self.warnings.append(message)
    
    def add_error(self, message: str) -> None:
        """エラーを追加"""
        self.errors.append(message)
        self.is_valid = False
    
    def calculate_overall_quality(self) -> float:
        """総合品質スコアを計算"""
        if not self.is_valid:
            return 0.0
        
        # 各指標の重み付き平均
        weights = {
            'readability': 0.3,
            'timing_accuracy': 0.3,
            'formatting_consistency': 0.2,
            'content_completeness': 0.2
        }
        
        content_completeness = 100.0 if self.character_count > 0 else 0.0
        
        quality_score = (
            self.readability_score * weights['readability'] +
            self.timing_accuracy * weights['timing_accuracy'] +
            self.formatting_consistency * weights['formatting_consistency'] +
            content_completeness * weights['content_completeness']
        )
        
        # エラー・警告によるペナルティ
        penalty = len(self.errors) * 10 + len(self.warnings) * 2
        quality_score = max(0.0, quality_score - penalty)
        
        self.quality_score = quality_score
        return quality_score
    
    def get_summary(self) -> Dict[str, Any]:
        """検証結果サマリーを取得"""
        return {
            'is_valid': self.is_valid,
            'quality_score': self.quality_score,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'total_duration': self.total_duration,
            'line_count': self.line_count,
            'character_count': self.character_count,
            'readability_score': self.readability_score,
            'timing_accuracy': self.timing_accuracy,
            'validation_time': self.validation_time.isoformat()
        }


@dataclass
class FileInfo:
    """ファイル情報"""
    file_path: str
    size_bytes: int = 0
    encoding: EncodingType = EncodingType.UTF8
    
    # ファイル属性
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    checksum_md5: str = ""
    checksum_sha256: str = ""
    
    # 内容情報
    line_count: int = 0
    character_count: int = 0
    byte_count: int = 0
    
    def __post_init__(self):
        """初期化後の処理"""
        if os.path.exists(self.file_path):
            self._update_file_stats()
    
    def _update_file_stats(self) -> None:
        """ファイル統計を更新"""
        try:
            stat = os.stat(self.file_path)
            self.size_bytes = stat.st_size
            self.created_at = datetime.fromtimestamp(stat.st_ctime)
            self.modified_at = datetime.fromtimestamp(stat.st_mtime)
            
            # チェックサム計算
            with open(self.file_path, 'rb') as f:
                content = f.read()
                self.checksum_md5 = hashlib.md5(content).hexdigest()
                self.checksum_sha256 = hashlib.sha256(content).hexdigest()
            
            # テキスト統計
            if self.file_path.endswith('.ass'):
                self._calculate_text_stats()
                
        except Exception as e:
            # ファイルアクセスエラーは静かに処理
            pass
    
    def _calculate_text_stats(self) -> None:
        """テキスト統計を計算"""
        try:
            with open(self.file_path, 'r', encoding=self.encoding.value) as f:
                content = f.read()
                self.character_count = len(content)
                self.line_count = len(content.splitlines())
                self.byte_count = len(content.encode(self.encoding.value))
        except:
            pass
    
    def verify_integrity(self) -> bool:
        """ファイル整合性を検証"""
        if not os.path.exists(self.file_path):
            return False
        
        try:
            with open(self.file_path, 'rb') as f:
                content = f.read()
                current_md5 = hashlib.md5(content).hexdigest()
                return current_md5 == self.checksum_md5
        except:
            return False
    
    def get_file_size_human(self) -> str:
        """人間が読みやすいファイルサイズを取得"""
        size = self.size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


@dataclass
class ASSMetadata:
    """ASS字幕メタデータ"""
    # スクリプト情報
    title: str = "Generated Subtitle"
    script_type: str = "v4.00+"
    wrap_style: int = 2
    play_res_x: int = 1080
    play_res_y: int = 1920
    scaled_border_and_shadow: str = "yes"
    ycbcr_matrix: str = "TV.709"
    
    # スタイル情報
    styles_count: int = 0
    events_count: int = 0
    total_duration: float = 0.0
    
    # 品質情報
    has_timing_overlaps: bool = False
    has_empty_lines: bool = False
    max_line_length: int = 0
    average_line_length: float = 0.0
    
    # 生成情報
    generator_name: str = "subtitle-generator"
    generator_version: str = "1.0.0"
    generation_time: datetime = field(default_factory=datetime.now)
    
    # カスタムメタデータ
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def to_ass_header(self) -> str:
        """ASSヘッダー文字列を生成"""
        header_lines = [
            "[Script Info]",
            f"Title: {self.title}",
            f"ScriptType: {self.script_type}",
            f"WrapStyle: {self.wrap_style}",
            f"PlayResX: {self.play_res_x}",
            f"PlayResY: {self.play_res_y}",
            f"ScaledBorderAndShadow: {self.scaled_border_and_shadow}",
            f"YCbCr Matrix: {self.ycbcr_matrix}",
            "",
            f"!: Generated by {self.generator_name} v{self.generator_version}",
            f"!: Generation time: {self.generation_time.isoformat()}",
            ""
        ]
        
        # カスタムフィールドを追加
        for key, value in self.custom_fields.items():
            header_lines.append(f"{key}: {value}")
        
        return "\n".join(header_lines)
    
    def update_stats(self, ass_content: str) -> None:
        """ASS内容から統計を更新"""
        lines = ass_content.split('\n')
        
        # イベント数をカウント
        self.events_count = sum(1 for line in lines if line.startswith('Dialogue:'))
        
        # スタイル数をカウント  
        style_section = False
        for line in lines:
            if line.startswith('[V4+ Styles]'):
                style_section = True
                continue
            elif line.startswith('[') and style_section:
                break
            elif style_section and line.startswith('Style:'):
                self.styles_count += 1
        
        # 行の長さ統計
        dialogue_lines = [line for line in lines if line.startswith('Dialogue:')]
        if dialogue_lines:
            lengths = []
            for line in dialogue_lines:
                parts = line.split(',', 9)
                if len(parts) >= 10:
                    text = parts[9]
                    # ASS効果タグを除外して実際のテキスト長を測定
                    import re
                    clean_text = re.sub(r'\\[^}]*}?', '', text)
                    lengths.append(len(clean_text))
            
            if lengths:
                self.max_line_length = max(lengths)
                self.average_line_length = sum(lengths) / len(lengths)


@dataclass
class ASSOutput:
    """ASS字幕出力の統一管理"""
    content: str
    metadata: ASSMetadata
    file_info: Optional[FileInfo] = None
    validation_result: Optional[ValidationResult] = None
    
    # 出力設定
    output_format: OutputFormat = OutputFormat.ASS
    encoding: EncodingType = EncodingType.UTF8
    
    # 最適化情報
    is_optimized: bool = False
    compression_level: CompressionLevel = CompressionLevel.NONE
    
    # 生成情報
    generation_time: datetime = field(default_factory=datetime.now)
    generation_duration_ms: float = 0.0
    
    def __post_init__(self):
        """初期化後の処理"""
        # メタデータの自動更新
        self.metadata.update_stats(self.content)
        
        # 基本検証の実行
        if not self.validation_result:
            self.validation_result = self._basic_validation()
    
    def _basic_validation(self) -> ValidationResult:
        """基本検証を実行"""
        result = ValidationResult()
        
        # 内容チェック
        if not self.content.strip():
            result.add_error("Empty ASS content")
            return result
        
        # 基本フォーマットチェック
        if "[Script Info]" not in self.content:
            result.add_error("Missing [Script Info] section")
        
        if "[V4+ Styles]" not in self.content:
            result.add_error("Missing [V4+ Styles] section")
        
        if "[Events]" not in self.content:
            result.add_error("Missing [Events] section")
        
        # 統計情報の設定
        result.line_count = self.metadata.events_count
        result.character_count = len(self.content)
        result.total_duration = self.metadata.total_duration
        
        if result.line_count > 0:
            result.average_line_duration = result.total_duration / result.line_count
        
        # 基本品質スコア
        result.readability_score = 85.0  # デフォルト値
        result.timing_accuracy = 90.0
        result.formatting_consistency = 95.0
        
        result.calculate_overall_quality()
        return result
    
    def save_to_file(self, file_path: str) -> bool:
        """ファイルに保存"""
        try:
            # ディレクトリ作成
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # ファイル書き込み
            with open(file_path, 'w', encoding=self.encoding.value) as f:
                f.write(self.content)
            
            # ファイル情報を更新
            self.file_info = FileInfo(file_path=file_path, encoding=self.encoding)
            
            return True
        except Exception as e:
            if self.validation_result:
                self.validation_result.add_error(f"File save error: {str(e)}")
            return False
    
    def validate(self, level: ValidationLevel = ValidationLevel.STANDARD) -> ValidationResult:
        """詳細検証を実行"""
        result = ValidationResult()
        
        # レベル別検証
        if level in [ValidationLevel.BASIC, ValidationLevel.STANDARD, ValidationLevel.STRICT]:
            result = self._basic_validation()
        
        if level in [ValidationLevel.STANDARD, ValidationLevel.STRICT]:
            self._standard_validation(result)
        
        if level == ValidationLevel.STRICT:
            self._strict_validation(result)
        
        self.validation_result = result
        return result
    
    def _standard_validation(self, result: ValidationResult) -> None:
        """標準検証"""
        lines = self.content.split('\n')
        dialogue_lines = [line for line in lines if line.startswith('Dialogue:')]
        
        # タイミング検証
        timings = []
        for line in dialogue_lines:
            parts = line.split(',', 9)
            if len(parts) >= 3:
                try:
                    start_time = self._parse_ass_time(parts[1])
                    end_time = self._parse_ass_time(parts[2])
                    if end_time <= start_time:
                        result.add_error(f"Invalid timing: {parts[1]} -> {parts[2]}")
                    timings.append((start_time, end_time))
                except:
                    result.add_error(f"Invalid time format: {parts[1]}, {parts[2]}")
        
        # 重複チェック
        for i, (start1, end1) in enumerate(timings):
            for j, (start2, end2) in enumerate(timings[i+1:], i+1):
                if not (end1 <= start2 or end2 <= start1):
                    result.add_warning(f"Timing overlap detected at lines {i+1} and {j+1}")
        
        # 品質指標の再計算
        if timings:
            result.timing_accuracy = 95.0 - len([w for w in result.warnings if 'overlap' in w]) * 5
        
        result.calculate_overall_quality()
    
    def _strict_validation(self, result: ValidationResult) -> None:
        """厳密検証"""
        # エンコーディング検証
        try:
            self.content.encode(self.encoding.value)
            result.encoding_valid = True
        except:
            result.add_error(f"Content cannot be encoded as {self.encoding.value}")
            result.encoding_valid = False
        
        # 文字数制限チェック（例：1行50文字以内）
        lines = self.content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('Dialogue:'):
                parts = line.split(',', 9)
                if len(parts) >= 10:
                    import re
                    clean_text = re.sub(r'\\[^}]*}?', '', parts[9])
                    if len(clean_text) > 50:
                        result.add_warning(f"Line {i+1} exceeds 50 characters: {len(clean_text)}")
        
        result.calculate_overall_quality()
    
    def _parse_ass_time(self, time_str: str) -> float:
        """ASS時間フォーマットを秒に変換"""
        parts = time_str.split(':')
        if len(parts) != 3:
            raise ValueError(f"Invalid time format: {time_str}")
        
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        
        return hours * 3600 + minutes * 60 + seconds
    
    def get_performance_info(self) -> Dict[str, Any]:
        """パフォーマンス情報を取得"""
        return {
            'generation_duration_ms': self.generation_duration_ms,
            'content_size_bytes': len(self.content.encode(self.encoding.value)),
            'events_count': self.metadata.events_count,
            'total_duration': self.metadata.total_duration,
            'compression_level': self.compression_level.value,
            'is_optimized': self.is_optimized
        }


@dataclass
class EncodingInfo:
    """エンコーディング情報"""
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    container_format: str = "mp4"
    
    # 品質設定
    crf: int = 23               # 品質値（0-51、低いほど高品質）
    preset: str = "fast"        # エンコードプリセット
    profile: str = "high"       # H.264プロファイル
    
    # ビットレート設定
    video_bitrate: Optional[str] = None  # "2M" など
    audio_bitrate: str = "128k"
    
    # フレーム設定
    fps: int = 30
    keyframe_interval: int = 30
    
    # 最適化
    two_pass: bool = False
    hardware_acceleration: bool = False
    gpu_device: Optional[str] = None
    
    def to_ffmpeg_params(self) -> List[str]:
        """FFmpegパラメータに変換"""
        params = [
            "-c:v", self.video_codec,
            "-preset", self.preset,
            "-profile:v", self.profile,
            "-crf", str(self.crf),
            "-r", str(self.fps),
            "-g", str(self.keyframe_interval)
        ]
        
        if self.video_bitrate:
            params.extend(["-b:v", self.video_bitrate])
        
        if self.audio_codec != "none":
            params.extend(["-c:a", self.audio_codec, "-b:a", self.audio_bitrate])
        
        if self.hardware_acceleration and self.gpu_device:
            params.extend(["-hwaccel", "auto", "-hwaccel_device", self.gpu_device])
        
        return params


@dataclass
class SyncInfo:
    """字幕同期情報"""
    subtitle_offset: float = 0.0     # 字幕オフセット（秒）
    video_duration: float = 0.0      # 動画長（秒）
    subtitle_duration: float = 0.0   # 字幕長（秒）
    
    # 同期品質
    sync_accuracy: float = 100.0     # 同期精度（%）
    timing_drift: float = 0.0        # タイミングドリフト（秒/分）
    
    # 調整情報
    auto_sync_applied: bool = False
    manual_adjustments: List[Tuple[float, float]] = field(default_factory=list)  # (時間, 調整量)
    
    def is_synchronized(self) -> bool:
        """同期が取れているかチェック"""
        return (abs(self.subtitle_offset) < 0.1 and 
                self.sync_accuracy > 95.0 and 
                abs(self.timing_drift) < 0.01)
    
    def get_sync_status(self) -> str:
        """同期ステータスを取得"""
        if self.is_synchronized():
            return "excellent"
        elif self.sync_accuracy > 85.0:
            return "good"
        elif self.sync_accuracy > 70.0:
            return "fair"
        else:
            return "poor"


@dataclass
class VideoOutput:
    """動画出力の管理"""
    file_path: str
    resolution: Tuple[int, int]
    duration: float
    
    # エンコーディング情報
    encoding_info: EncodingInfo = field(default_factory=EncodingInfo)
    file_info: Optional[FileInfo] = None
    
    # 字幕同期
    subtitle_sync: SyncInfo = field(default_factory=SyncInfo)
    subtitle_file_path: Optional[str] = None
    
    # 品質・パフォーマンス
    encoding_time_ms: float = 0.0
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    
    # 出力状態
    is_completed: bool = False
    has_audio: bool = False
    
    def __post_init__(self):
        """初期化後の処理"""
        if os.path.exists(self.file_path):
            self.file_info = FileInfo(file_path=self.file_path)
            self.is_completed = True
            self._analyze_video()
    
    def _analyze_video(self) -> None:
        """動画ファイルを分析"""
        # 実際の実装では ffprobe などを使用
        # ここでは基本的な情報のみ設定
        if self.file_info and self.file_info.size_bytes > 0:
            self.quality_metrics['file_size_mb'] = self.file_info.size_bytes / (1024 * 1024)
            self.quality_metrics['compression_ratio'] = self._estimate_compression_ratio()
    
    def _estimate_compression_ratio(self) -> float:
        """圧縮率を推定"""
        if not self.file_info:
            return 0.0
        
        # 理論的な非圧縮サイズを推定
        width, height = self.resolution
        fps = self.encoding_info.fps
        theoretical_size = width * height * 3 * fps * self.duration  # RGB24
        
        if theoretical_size > 0:
            return self.file_info.size_bytes / theoretical_size
        return 0.0
    
    def verify_output(self) -> bool:
        """出力ファイルを検証"""
        if not os.path.exists(self.file_path):
            return False
        
        if not self.file_info:
            self.file_info = FileInfo(file_path=self.file_path)
        
        # 基本的な検証
        return (self.file_info.size_bytes > 1000 and  # 最小サイズチェック
                self.file_info.verify_integrity())
    
    def get_output_info(self) -> Dict[str, Any]:
        """出力情報を取得"""
        return {
            'file_path': self.file_path,
            'resolution': f"{self.resolution[0]}x{self.resolution[1]}",
            'duration': self.duration,
            'file_size': self.file_info.get_file_size_human() if self.file_info else "Unknown",
            'encoding_time_ms': self.encoding_time_ms,
            'is_completed': self.is_completed,
            'has_audio': self.has_audio,
            'sync_status': self.subtitle_sync.get_sync_status(),
            'quality_metrics': self.quality_metrics
        }


@dataclass  
class PerformanceMetrics:
    """パフォーマンスメトリクス"""
    # 時間測定
    total_time_ms: float = 0.0
    text_processing_time_ms: float = 0.0
    effect_processing_time_ms: float = 0.0
    rendering_time_ms: float = 0.0
    file_io_time_ms: float = 0.0
    
    # メモリ使用量
    peak_memory_mb: float = 0.0
    average_memory_mb: float = 0.0
    
    # 処理量
    characters_processed: int = 0
    lines_processed: int = 0
    effects_applied: int = 0
    
    # スループット
    characters_per_second: float = 0.0
    lines_per_second: float = 0.0
    
    # システムリソース
    cpu_usage_percent: float = 0.0
    disk_io_mb: float = 0.0
    
    def calculate_throughput(self) -> None:
        """スループットを計算"""
        if self.total_time_ms > 0:
            time_seconds = self.total_time_ms / 1000
            self.characters_per_second = self.characters_processed / time_seconds
            self.lines_per_second = self.lines_processed / time_seconds
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """パフォーマンスサマリーを取得"""
        return {
            'total_time_seconds': self.total_time_ms / 1000,
            'peak_memory_mb': self.peak_memory_mb,
            'characters_per_second': self.characters_per_second,
            'lines_per_second': self.lines_per_second,
            'cpu_usage_percent': self.cpu_usage_percent,
            'processing_breakdown': {
                'text_processing': self.text_processing_time_ms / 1000,
                'effect_processing': self.effect_processing_time_ms / 1000,
                'rendering': self.rendering_time_ms / 1000,
                'file_io': self.file_io_time_ms / 1000
            }
        }


@dataclass
class GenerationError:
    """生成エラー情報"""
    error_type: str
    message: str
    location: str = ""
    
    # エラー詳細
    error_code: Optional[str] = None
    severity: str = "error"  # "warning", "error", "critical"
    
    # コンテキスト情報
    line_number: Optional[int] = None
    character_position: Optional[int] = None
    function_name: Optional[str] = None
    stack_trace: Optional[str] = None
    
    # 修復情報
    is_recoverable: bool = False
    suggested_fix: Optional[str] = None
    
    # 時刻情報
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'error_type': self.error_type,
            'message': self.message,
            'location': self.location,
            'error_code': self.error_code,
            'severity': self.severity,
            'line_number': self.line_number,
            'character_position': self.character_position,
            'function_name': self.function_name,
            'is_recoverable': self.is_recoverable,
            'suggested_fix': self.suggested_fix,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class GenerationResult:
    """生成結果の統合管理"""
    success: bool
    
    # 出力結果
    ass_output: Optional[ASSOutput] = None
    video_output: Optional[VideoOutput] = None
    
    # パフォーマンス・品質
    performance_metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    errors: List[GenerationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # 生成情報
    generation_id: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    # 設定情報
    config_used: Dict[str, Any] = field(default_factory=dict)
    template_name: str = ""
    
    def __post_init__(self):
        """初期化後の処理"""
        if not self.generation_id:
            self.generation_id = self._generate_id()
    
    def _generate_id(self) -> str:
        """一意のIDを生成"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def mark_completed(self) -> None:
        """完了マーク"""
        self.end_time = datetime.now()
        if self.performance_metrics:
            total_ms = (self.end_time - self.start_time).total_seconds() * 1000
            self.performance_metrics.total_time_ms = total_ms
            self.performance_metrics.calculate_throughput()
    
    def add_error(self, error_type: str, message: str, **kwargs) -> None:
        """エラーを追加"""
        error = GenerationError(
            error_type=error_type,
            message=message,
            **kwargs
        )
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, message: str) -> None:
        """警告を追加"""
        self.warnings.append(message)
    
    def get_overall_quality_score(self) -> float:
        """総合品質スコアを取得"""
        scores = []
        
        if self.ass_output and self.ass_output.validation_result:
            scores.append(self.ass_output.validation_result.quality_score)
        
        if self.video_output:
            # 動画品質の簡易評価
            video_score = 85.0  # ベース
            if self.video_output.subtitle_sync.is_synchronized():
                video_score += 10.0
            scores.append(video_score)
        
        if scores:
            overall_score = sum(scores) / len(scores)
            
            # エラー・警告によるペナルティ
            penalty = len(self.errors) * 10 + len(self.warnings) * 2
            return max(0.0, overall_score - penalty)
        
        return 0.0 if not self.success else 50.0
    
    def get_summary(self) -> Dict[str, Any]:
        """結果サマリーを取得"""
        summary = {
            'generation_id': self.generation_id,
            'success': self.success,
            'template_name': self.template_name,
            'overall_quality_score': self.get_overall_quality_score(),
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None
        }
        
        if self.ass_output:
            summary['ass_output'] = {
                'events_count': self.ass_output.metadata.events_count,
                'total_duration': self.ass_output.metadata.total_duration,
                'quality_score': self.ass_output.validation_result.quality_score if self.ass_output.validation_result else 0,
                'file_size': self.ass_output.file_info.get_file_size_human() if self.ass_output.file_info else "Unknown"
            }
        
        if self.video_output:
            summary['video_output'] = self.video_output.get_output_info()
        
        if self.performance_metrics:
            summary['performance'] = self.performance_metrics.get_performance_summary()
        
        return summary
    
    def save_report(self, file_path: str) -> bool:
        """結果レポートを保存"""
        try:
            import json
            
            report = {
                'summary': self.get_summary(),
                'errors': [error.to_dict() for error in self.errors],
                'warnings': self.warnings,
                'config_used': self.config_used
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception:
            return False


# ユーティリティ関数

def create_ass_output(content: str, title: str = "Generated Subtitle", 
                     resolution: Tuple[int, int] = (1080, 1920)) -> ASSOutput:
    """ASSOutput を作成"""
    metadata = ASSMetadata(
        title=title,
        play_res_x=resolution[0],
        play_res_y=resolution[1]
    )
    
    return ASSOutput(
        content=content,
        metadata=metadata
    )


def create_video_output(file_path: str, resolution: Tuple[int, int], 
                       duration: float, subtitle_path: Optional[str] = None) -> VideoOutput:
    """VideoOutput を作成"""
    video_output = VideoOutput(
        file_path=file_path,
        resolution=resolution,
        duration=duration,
        subtitle_file_path=subtitle_path
    )
    
    if subtitle_path:
        video_output.subtitle_sync.subtitle_duration = duration
        video_output.subtitle_sync.video_duration = duration
    
    return video_output


def create_generation_result(success: bool = True, template_name: str = "") -> GenerationResult:
    """GenerationResult を作成"""
    return GenerationResult(
        success=success,
        template_name=template_name
    )