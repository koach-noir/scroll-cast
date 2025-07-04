"""
Video Generator
FFmpegを使用した動画生成ユーティリティ
"""

import os
import subprocess
from typing import Tuple, Optional


class VideoGenerator:
    """動画生成クラス"""
    
    def __init__(self, default_resolution: Tuple[int, int] = (1080, 1920)):
        """
        Args:
            default_resolution: デフォルト解像度 (width, height)
        """
        self.default_resolution = default_resolution
    
    def create_video_with_subtitles(self, ass_file_path: str, output_path: str, 
                                   duration: float, resolution: Optional[Tuple[int, int]] = None,
                                   background_color: str = "black", fps: int = 30,
                                   quality_preset: str = "fast", crf: int = 23) -> bool:
        """字幕付き動画を生成
        
        Args:
            ass_file_path: ASSファイルのパス
            output_path: 出力動画ファイルのパス
            duration: 動画の長さ（秒）
            resolution: 解像度 (width, height)
            background_color: 背景色
            fps: フレームレート
            quality_preset: 品質プリセット
            crf: 品質値 (0-51, 低いほど高品質)
        
        Returns:
            動画生成成功の可否
        """
        if resolution is None:
            resolution = self.default_resolution
        
        width, height = resolution
        
        try:
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c={background_color}:size={width}x{height}:duration={duration}",
                "-vf", f"subtitles={ass_file_path}",
                "-c:v", "libx264",
                "-preset", quality_preset,
                "-crf", str(crf),
                "-pix_fmt", "yuv420p",
                "-r", str(fps),
                "-t", str(duration),
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ 動画ファイル生成完了: {output_path}")
                return True
            else:
                print(f"❌ FFmpegエラー: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 動画生成エラー: {e}")
            return False
    
    def create_greenscreen_video(self, ass_file_path: str, output_path: str,
                               duration: float, resolution: Optional[Tuple[int, int]] = None) -> bool:
        """グリーンスクリーン動画を生成（TikTok用など）
        
        Args:
            ass_file_path: ASSファイルのパス
            output_path: 出力動画ファイルのパス
            duration: 動画の長さ（秒）
            resolution: 解像度 (width, height)
        
        Returns:
            動画生成成功の可否
        """
        return self.create_video_with_subtitles(
            ass_file_path=ass_file_path,
            output_path=output_path,
            duration=duration,
            resolution=resolution,
            background_color="#00FF00"  # Green
        )
    
    def create_transparent_video(self, ass_file_path: str, output_path: str,
                               duration: float, resolution: Optional[Tuple[int, int]] = None) -> bool:
        """透明背景動画を生成（編集ソフト用）
        
        Args:
            ass_file_path: ASSファイルのパス
            output_path: 出力動画ファイルのパス
            duration: 動画の長さ（秒）
            resolution: 解像度 (width, height)
        
        Returns:
            動画生成成功の可否
        """
        if resolution is None:
            resolution = self.default_resolution
        
        width, height = resolution
        
        try:
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c=0x00000000:size={width}x{height}:duration={duration}",
                "-vf", f"subtitles={ass_file_path}",
                "-c:v", "prores_ks",
                "-profile:v", "4444",
                "-pix_fmt", "yuva444p10le",
                "-t", str(duration),
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ 透明背景動画生成完了: {output_path}")
                return True
            else:
                print(f"❌ FFmpegエラー: {result.stderr}")
                print("ProRes codecが利用できない可能性があります")
                return False
                
        except Exception as e:
            print(f"❌ 透明背景動画生成エラー: {e}")
            return False
    
    def get_video_info(self, video_path: str) -> Optional[dict]:
        """動画ファイルの情報を取得
        
        Args:
            video_path: 動画ファイルのパス
        
        Returns:
            動画情報の辞書またはNone
        """
        try:
            cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                import json
                return json.loads(result.stdout)
            else:
                return None
                
        except Exception:
            return None
    
    @staticmethod
    def check_ffmpeg_available() -> bool:
        """FFmpegが利用可能かチェック
        
        Returns:
            FFmpegが利用可能かどうか
        """
        try:
            result = subprocess.run(["ffmpeg", "-version"], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False