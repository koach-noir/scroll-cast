"""
Monitoring System
リアルタイムメトリクス収集・監視システム
"""

import time
import psutil
import threading
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import json
import os
from pathlib import Path

from .models.output_models import ValidationResult, PerformanceMetrics, GenerationResult


class MetricType(Enum):
    """メトリクス種別"""
    PERFORMANCE = "performance"
    QUALITY = "quality"
    SYSTEM = "system"
    BUSINESS = "business"


class AlertLevel(Enum):
    """アラートレベル"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricPoint:
    """メトリクス測定点"""
    timestamp: datetime
    metric_name: str
    value: float
    metric_type: MetricType
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'metric_name': self.metric_name,
            'value': self.value,
            'metric_type': self.metric_type.value,
            'metadata': self.metadata
        }


@dataclass
class SystemMetrics:
    """システムメトリクス"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    process_count: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'memory_used_mb': self.memory_used_mb,
            'disk_usage_percent': self.disk_usage_percent,
            'process_count': self.process_count,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class Alert:
    """アラート情報"""
    id: str
    level: AlertLevel
    message: str
    metric_name: str
    current_value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'id': self.id,
            'level': self.level.value,
            'message': self.message,
            'metric_name': self.metric_name,
            'current_value': self.current_value,
            'threshold': self.threshold,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved
        }


class PerformanceMonitor:
    """パフォーマンス監視クラス"""
    
    def __init__(self):
        self.metrics: List[MetricPoint] = []
        self.system_metrics: List[SystemMetrics] = []
        self.alerts: List[Alert] = []
        self.thresholds: Dict[str, Dict[str, float]] = {}
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # デフォルトの閾値設定
        self._set_default_thresholds()
    
    def _set_default_thresholds(self):
        """デフォルト閾値を設定"""
        self.thresholds = {
            'processing_time': {'warning': 10.0, 'error': 30.0},
            'memory_usage_mb': {'warning': 500.0, 'error': 1000.0},
            'cpu_percent': {'warning': 80.0, 'error': 95.0},
            'quality_score': {'warning': 70.0, 'error': 50.0},
            'error_rate': {'warning': 0.05, 'error': 0.1}
        }
    
    def start_monitoring(self, interval: float = 1.0):
        """監視を開始"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """監視を停止"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
    
    def _monitor_loop(self, interval: float):
        """監視ループ"""
        while self.monitoring_active:
            try:
                # システムメトリクス取得
                system_metrics = self._collect_system_metrics()
                
                with self.lock:
                    self.system_metrics.append(system_metrics)
                    
                    # 古いデータを削除（24時間分保持）
                    cutoff = datetime.now() - timedelta(hours=24)
                    self.system_metrics = [m for m in self.system_metrics if m.timestamp > cutoff]
                
                # アラートチェック
                self._check_system_alerts(system_metrics)
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"監視エラー: {e}")
                time.sleep(interval)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """システムメトリクスを収集"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / 1024 / 1024,
            disk_usage_percent=disk.percent,
            process_count=len(psutil.pids())
        )
    
    def _check_system_alerts(self, metrics: SystemMetrics):
        """システムアラートをチェック"""
        checks = [
            ('cpu_percent', metrics.cpu_percent),
            ('memory_percent', metrics.memory_percent),
        ]
        
        for metric_name, value in checks:
            if metric_name in self.thresholds:
                self._check_threshold(metric_name, value)
    
    def record_metric(self, name: str, value: float, metric_type: MetricType, metadata: Optional[Dict[str, Any]] = None):
        """メトリクスを記録"""
        point = MetricPoint(
            timestamp=datetime.now(),
            metric_name=name,
            value=value,
            metric_type=metric_type,
            metadata=metadata or {}
        )
        
        with self.lock:
            self.metrics.append(point)
            
            # 古いデータを削除（24時間分保持）
            cutoff = datetime.now() - timedelta(hours=24)
            self.metrics = [m for m in self.metrics if m.timestamp > cutoff]
        
        # 閾値チェック
        self._check_threshold(name, value)
    
    def _check_threshold(self, metric_name: str, value: float):
        """閾値チェック"""
        if metric_name not in self.thresholds:
            return
        
        thresholds = self.thresholds[metric_name]
        
        if 'error' in thresholds and value >= thresholds['error']:
            self._create_alert(metric_name, value, thresholds['error'], AlertLevel.ERROR)
        elif 'warning' in thresholds and value >= thresholds['warning']:
            self._create_alert(metric_name, value, thresholds['warning'], AlertLevel.WARNING)
    
    def _create_alert(self, metric_name: str, value: float, threshold: float, level: AlertLevel):
        """アラートを作成"""
        alert_id = f"{metric_name}_{level.value}_{int(time.time())}"
        
        # 同じメトリクス・レベルで未解決のアラートがある場合はスキップ
        existing = [a for a in self.alerts if a.metric_name == metric_name and a.level == level and not a.resolved]
        if existing:
            return
        
        alert = Alert(
            id=alert_id,
            level=level,
            message=f"{metric_name} が閾値を超過: {value:.2f} >= {threshold:.2f}",
            metric_name=metric_name,
            current_value=value,
            threshold=threshold
        )
        
        with self.lock:
            self.alerts.append(alert)
    
    def get_metrics(self, metric_name: Optional[str] = None, since: Optional[datetime] = None) -> List[MetricPoint]:
        """メトリクスを取得"""
        with self.lock:
            result = self.metrics.copy()
        
        if metric_name:
            result = [m for m in result if m.metric_name == metric_name]
        
        if since:
            result = [m for m in result if m.timestamp >= since]
        
        return result
    
    def get_system_metrics(self, since: Optional[datetime] = None) -> List[SystemMetrics]:
        """システムメトリクスを取得"""
        with self.lock:
            result = self.system_metrics.copy()
        
        if since:
            result = [m for m in result if m.timestamp >= since]
        
        return result
    
    def get_alerts(self, level: Optional[AlertLevel] = None, resolved: Optional[bool] = None) -> List[Alert]:
        """アラートを取得"""
        with self.lock:
            result = self.alerts.copy()
        
        if level:
            result = [a for a in result if a.level == level]
        
        if resolved is not None:
            result = [a for a in result if a.resolved == resolved]
        
        return result
    
    def resolve_alert(self, alert_id: str):
        """アラートを解決済みにマーク"""
        with self.lock:
            for alert in self.alerts:
                if alert.id == alert_id:
                    alert.resolved = True
                    break
    
    def export_metrics(self, file_path: str):
        """メトリクスをファイルにエクスポート"""
        data = {
            'metrics': [m.to_dict() for m in self.metrics],
            'system_metrics': [m.to_dict() for m in self.system_metrics],
            'alerts': [a.to_dict() for a in self.alerts],
            'exported_at': datetime.now().isoformat()
        }
        
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def clear_old_data(self, hours: int = 24):
        """古いデータをクリア"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            self.metrics = [m for m in self.metrics if m.timestamp > cutoff]
            self.system_metrics = [m for m in self.system_metrics if m.timestamp > cutoff]
            # アラートは削除しない（解決済みのみ削除対象にする場合）
            self.alerts = [a for a in self.alerts if not a.resolved or a.timestamp > cutoff]
    
    def get_summary(self) -> Dict[str, Any]:
        """監視サマリーを取得"""
        with self.lock:
            recent_cutoff = datetime.now() - timedelta(minutes=5)
            recent_metrics = [m for m in self.metrics if m.timestamp > recent_cutoff]
            unresolved_alerts = [a for a in self.alerts if not a.resolved]
            
            # 最新のシステムメトリクス
            latest_system = self.system_metrics[-1] if self.system_metrics else None
            
            return {
                'monitoring_active': self.monitoring_active,
                'total_metrics': len(self.metrics),
                'recent_metrics': len(recent_metrics),
                'total_alerts': len(self.alerts),
                'unresolved_alerts': len(unresolved_alerts),
                'latest_system_metrics': latest_system.to_dict() if latest_system else None,
                'summary_time': datetime.now().isoformat()
            }


class QualityMonitor:
    """品質監視クラス"""
    
    def __init__(self, performance_monitor: PerformanceMonitor):
        self.performance_monitor = performance_monitor
        self.quality_history: List[Dict[str, Any]] = []
        self.baseline_quality: Optional[float] = None
    
    def record_generation_result(self, result: GenerationResult):
        """生成結果を記録"""
        if not result.success:
            # エラー率を記録
            self.performance_monitor.record_metric(
                'error_rate', 1.0, MetricType.QUALITY,
                {'errors': [str(e) for e in result.errors]}
            )
            return
        
        # 品質スコアを記録
        overall_quality = result.get_overall_quality_score()
        self.performance_monitor.record_metric(
            'quality_score', overall_quality, MetricType.QUALITY,
            {'generation_id': result.generation_id}
        )
        
        # 処理時間を記録
        if result.performance_metrics:
            self.performance_monitor.record_metric(
                'processing_time', result.performance_metrics.total_time_ms / 1000.0, MetricType.PERFORMANCE,
                {'generation_id': result.generation_id}
            )
            
            self.performance_monitor.record_metric(
                'memory_usage_mb', result.performance_metrics.peak_memory_mb, MetricType.PERFORMANCE,
                {'generation_id': result.generation_id}
            )
        
        # 品質履歴に追加
        self.quality_history.append({
            'timestamp': datetime.now(),
            'quality_score': overall_quality,
            'generation_id': result.generation_id,
            'template_name': result.template_name if hasattr(result, 'template_name') else 'unknown'
        })
        
        # ベースライン品質の更新
        self._update_baseline_quality(overall_quality)
    
    def _update_baseline_quality(self, quality_score: float):
        """ベースライン品質を更新"""
        if self.baseline_quality is None:
            self.baseline_quality = quality_score
        else:
            # 指数移動平均で更新
            alpha = 0.1
            self.baseline_quality = alpha * quality_score + (1 - alpha) * self.baseline_quality
    
    def get_quality_trend(self, hours: int = 24) -> Dict[str, Any]:
        """品質トレンドを取得"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_quality = [q for q in self.quality_history if q['timestamp'] > cutoff]
        
        if not recent_quality:
            return {'trend': 'no_data', 'data_points': 0}
        
        scores = [q['quality_score'] for q in recent_quality]
        
        return {
            'trend': 'improving' if scores[-1] > scores[0] else 'declining',
            'data_points': len(scores),
            'average_quality': sum(scores) / len(scores),
            'min_quality': min(scores),
            'max_quality': max(scores),
            'baseline_quality': self.baseline_quality,
            'latest_quality': scores[-1] if scores else None
        }


# グローバル監視インスタンス
_global_monitor: Optional[PerformanceMonitor] = None
_global_quality_monitor: Optional[QualityMonitor] = None


def get_monitor() -> PerformanceMonitor:
    """グローバル監視インスタンスを取得"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
        _global_monitor.start_monitoring()
    return _global_monitor


def get_quality_monitor() -> QualityMonitor:
    """グローバル品質監視インスタンスを取得"""
    global _global_quality_monitor
    if _global_quality_monitor is None:
        _global_quality_monitor = QualityMonitor(get_monitor())
    return _global_quality_monitor


def shutdown_monitoring():
    """監視システムをシャットダウン"""
    global _global_monitor
    if _global_monitor:
        _global_monitor.stop_monitoring()