"""
CLI Main Entry Point
コマンドラインインターフェースのメインエントリーポイント
"""

import sys
import os
from typing import Dict, Any, Optional
from .parser import create_cli_parser


def main():
    """メインエントリーポイント"""
    try:
        # CLI引数を解析
        parser = create_cli_parser()
        args = parser.parse_args()
        
        
        # テンプレートエンジンを初期化
        from ..template_engine import TemplateEngine
        engine = TemplateEngine()
        
        # 引数から情報を抽出
        template_name = args['template']
        text = args['text']
        output_path = args['output']
        ass_output = args.get('ass_output')
        resolution = args['resolution']
        html_only = args.get('html_only', False)
        ass_only = args.get('ass_only', False)
        video_only = args.get('video_only', False)
        preset = args.get('preset')
        
        # 出力ファイルの拡張子に基づいて自動的にモードを判定
        output_ext = os.path.splitext(output_path)[1].lower()
        
        # 拡張子がない場合はHTMLをデフォルトとして追加
        if output_ext == '':
            output_path = f"{output_path}.html"
            output_ext = '.html'
            print(f"🌐 拡張子なし: HTML生成モードに自動設定 ({output_path})")
        
        if not html_only and not ass_only and not video_only:
            if output_ext == '.mp4' or output_ext == '.avi' or output_ext == '.mov':
                video_only = True
                print(f"🎬 拡張子 '{output_ext}' を検出: 動画生成モードに自動設定")
            elif output_ext == '.ass':
                ass_only = True
                print(f"📝 拡張子 '{output_ext}' を検出: ASS字幕生成モードに自動設定")
            elif output_ext == '.html':
                html_only = False  # デフォルトのHTML+ASS生成
                print(f"🌐 拡張子 '{output_ext}' を検出: HTML+ASS生成モードに自動設定")
            else:
                print(f"⚠️  未知の拡張子 '{output_ext}': デフォルトのHTML+ASS生成モードを使用")
        
        # テンプレート固有パラメータを抽出
        template_params = extract_template_parameters(args, engine, template_name)
        
        print(f"🎬 scroll-cast生成開始")
        print(f"   テンプレート: {template_name}")
        if preset:
            print(f"   プリセット: {preset}")
        print(f"   テキスト: {text[:50]}{'...' if len(text) > 50 else ''}")
        print(f"   出力: {output_path}")
        
        # 解像度を解析
        if isinstance(resolution, tuple):
            resolution_tuple = resolution
        else:
            resolution_tuple = tuple(map(int, resolution.split('x')))
        
        # 出力ディレクトリの作成
        output_dir = os.path.dirname(output_path)
        if output_dir:  # ディレクトリが存在する場合のみ作成
            os.makedirs(output_dir, exist_ok=True)
        
        if ass_only:
            # ASSファイルのみ生成
            ass_path = ass_output or f"{os.path.splitext(output_path)[0]}.ass"
            ass_dir = os.path.dirname(ass_path)
            if ass_dir:  # ディレクトリが存在する場合のみ作成
                os.makedirs(ass_dir, exist_ok=True)
            success = engine.generate_subtitle(
                template_name=template_name,
                text=text,
                output_path=ass_path,
                resolution=resolution_tuple,
                preset=preset,
                **template_params
            )
            
            if success:
                print(f"✅ ASS字幕ファイル生成完了: {ass_path}")
            else:
                print(f"❌ ASS字幕ファイル生成失敗")
                sys.exit(1)
        
        elif html_only:
            # HTMLファイルのみ生成
            success = generate_html_file(
                engine=engine,
                template_name=template_name,
                text=text,
                output_path=output_path,
                resolution=resolution_tuple,
                ass_file_path=None,  # HTML単体生成時は新規ASS生成
                preset=preset,
                **template_params
            )
            
            if success:
                print(f"✅ HTMLファイル生成完了: {output_path}")
            else:
                print(f"❌ HTMLファイル生成失敗")
                sys.exit(1)
        
        elif video_only:
            # 動画ファイルのみ生成
            # 出力パスの調整
            if output_path.startswith('output-default/output'):
                # デフォルトパスの場合、動画用ディレクトリに変更
                video_output_path = 'output-default/video/output.mp4'
            elif output_ext in ['.mp4', '.avi', '.mov']:
                # 既に動画拡張子が指定されている場合はそのまま使用
                video_output_path = output_path
            else:
                # その他の場合、拡張子を.mp4に変更
                base_path = os.path.splitext(output_path)[0]
                video_output_path = f"{base_path}.mp4"
            
            # 動画出力ディレクトリの作成
            video_output_dir = os.path.dirname(video_output_path)
            if video_output_dir:  # ディレクトリが存在する場合のみ作成
                os.makedirs(video_output_dir, exist_ok=True)
            
            success = generate_video_file(
                engine=engine,
                template_name=template_name,
                text=text,
                output_path=video_output_path,
                resolution=resolution_tuple,
                ass_file_path=None,  # 動画単体生成時は新規ASS生成
                preset=preset,
                **template_params
            )
            
            if success:
                print(f"✅ 動画ファイル生成完了: {video_output_path}")
            else:
                print(f"❌ 動画ファイル生成失敗")
                sys.exit(1)
        
        else:
            # HTML + ASS生成
            if ass_output:
                ass_path = ass_output
            else:
                # デフォルト: output-default/ass/ に配置
                base_name = os.path.splitext(os.path.basename(output_path))[0]
                ass_path = f"output-default/ass/{base_name}.ass"
            
            # ASS出力ディレクトリの作成
            ass_dir = os.path.dirname(ass_path)
            if ass_dir:  # ディレクトリが存在する場合のみ作成
                os.makedirs(ass_dir, exist_ok=True)
            
            # ASS生成
            success_ass = engine.generate_subtitle(
                template_name=template_name,
                text=text,
                output_path=ass_path,
                resolution=resolution_tuple,
                preset=preset,
                **template_params
            )
            
            # HTML生成（packingで生成済みのASSファイルを使用）
            success_html = generate_html_file(
                engine=engine,
                template_name=template_name,
                text=text,
                output_path=output_path,
                resolution=resolution_tuple,
                ass_file_path=ass_path,  # packingから生成されたASSファイルパス
                preset=preset,
                **template_params
            )
            
            if success_ass and success_html:
                print(f"✅ ファイル生成完了:")
                print(f"   HTML: {output_path}")
                print(f"   ASS:  {ass_path}")
            else:
                print(f"❌ ファイル生成失敗")
                sys.exit(1)
        
        print(f"🎯 処理完了!")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  処理がユーザーによって中断されました")
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def generate_video_file(engine, template_name: str, text: str, output_path: str, resolution: tuple, 
                       ass_file_path: Optional[str] = None, preset: Optional[str] = None, **template_params) -> bool:
    """動画ファイルを生成
    
    Args:
        engine: テンプレートエンジン
        template_name: テンプレート名
        text: 入力テキスト
        output_path: 出力動画ファイルパス
        resolution: 解像度
        ass_file_path: 既存のASSファイルパス（指定時はこれを使用、未指定時は新規生成）
        preset: プリセット名
        **template_params: テンプレート固有パラメータ
    
    Returns:
        生成成功の可否
    """
    try:
        # ASSファイルパスの決定
        if ass_file_path and os.path.exists(ass_file_path):
            # 既存のASSファイルを使用（packingから生成されたもの）
            ass_path = ass_file_path
            print(f"✅ 既存ASSファイルを使用: {ass_path}")
        else:
            # 一時ASSファイルを新規生成
            ass_path = f"{os.path.splitext(output_path)[0]}.ass"
            print(f"⚠️  新規ASSファイルを生成: {ass_path}")
            
            # ASS生成
            success_ass = engine.generate_subtitle(
                template_name=template_name,
                text=text,
                output_path=ass_path,
                resolution=resolution,
                preset=preset,
                **template_params
            )
            
            if not success_ass:
                return False
        
        # 動画生成
        success_video = engine.generate_video(
            template_name=template_name,
            text=text,
            output_path=output_path,
            ass_path=ass_path,
            resolution=resolution,
            preset=preset,
            **template_params
        )
        
        return success_video
        
    except Exception as e:
        print(f"❌ 動画生成エラー: {e}")
        return False


def generate_html_file(engine, template_name: str, text: str, output_path: str, resolution: tuple, 
                      ass_file_path: Optional[str] = None, preset: Optional[str] = None, **template_params) -> bool:
    """HTMLファイルを生成
    
    Args:
        engine: テンプレートエンジン
        template_name: テンプレート名
        text: 入力テキスト
        output_path: 出力HTMLファイルパス
        resolution: 解像度
        ass_file_path: 既存のASSファイルパス（指定時はこれを使用、未指定時は新規生成）
        preset: プリセット名
        **template_params: テンプレート固有パラメータ
    
    Returns:
        生成成功の可否
    """
    try:
        # ASS to HTML conversion using the conversion system
        from ...conversion.hierarchical_template_converter import HierarchicalTemplateConverter
        
        # ASSファイルパスの決定
        if ass_file_path and os.path.exists(ass_file_path):
            # 既存のASSファイルを使用（packingから生成されたもの）
            ass_path = ass_file_path
            print(f"✅ 既存ASSファイルを使用: {ass_path}")
        else:
            # 一時ASSファイルを新規生成
            ass_path = f"{os.path.splitext(output_path)[0]}.ass"
            print(f"⚠️  新規ASSファイルを生成: {ass_path}")
            
            # ASS生成
            success_ass = engine.generate_subtitle(
                template_name=template_name,
                text=text,
                output_path=ass_path,
                resolution=resolution,
                preset=preset,
                **template_params
            )
            
            if not success_ass:
                return False
        
        # HTML変換
        converter = HierarchicalTemplateConverter(template_name)
        converter.convert_ass_to_html(ass_path, output_path)
        
        return True
        
    except Exception as e:
        print(f"❌ HTML生成エラー: {e}")
        return False


def extract_template_parameters(args: Dict[str, Any], engine, template_name: str) -> Dict[str, Any]:
    """引数からテンプレート固有パラメータを抽出
    
    Args:
        args: 解析済み引数
        engine: テンプレートエンジン
        template_name: テンプレート名
    
    Returns:
        テンプレート固有パラメータの辞書
    """
    template = engine.get_template(template_name)
    if not template:
        return {}
    
    template_params = {}
    available_params = template.list_parameters()
    
    # 共通パラメータを除外
    common_params = {'font_size', 'resolution'}
    
    # プリセットが指定されている場合、デフォルト値を除外する
    preset_specified = args.get('preset') is not None
    
    # 引数からテンプレート固有パラメータを抽出
    for key, value in args.items():
        # CLI引数名をパラメータ名に変換（ハイフンをアンダースコアに）
        param_name = key.replace('-', '_')
        
        if param_name in available_params and param_name not in common_params:
            # プリセットが指定されている場合、デフォルト値をスキップ
            if preset_specified:
                param_info = template.get_parameter_info(param_name)
                if param_info and value == param_info.default:
                    continue  # デフォルト値はスキップ
            template_params[param_name] = value
    
    # font_sizeも追加（共通パラメータ）
    if 'font_size' in args:
        # プリセットが指定されている場合、デフォルト値（64）をスキップ
        if preset_specified and args['font_size'] == 64:
            pass  # デフォルト値はスキップ
        else:
            template_params['font_size'] = args['font_size']
    
    return template_params


def check_dependencies():
    """依存関係をチェック"""
    # FFmpegの確認
    from ...rendering.video_generator import VideoGenerator
    if not VideoGenerator.check_ffmpeg_available():
        print("⚠️  警告: FFmpegが見つかりません")
        print("   動画生成にはFFmpegが必要です")
        print("   インストール方法: https://ffmpeg.org/download.html")
        return False
    
    return True


if __name__ == "__main__":
    main()