"""
CLI Main Entry Point
コマンドラインインターフェースのメインエントリーポイント
"""

import sys
import os
from typing import Dict, Any
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
        no_video = args.get('no_video', False)
        
        # テンプレート固有パラメータを抽出
        template_params = extract_template_parameters(args, engine, template_name)
        
        print(f"🎬 字幕動画生成開始")
        print(f"   テンプレート: {template_name}")
        print(f"   テキスト: {text[:50]}{'...' if len(text) > 50 else ''}")
        print(f"   出力: {output_path}")
        
        if no_video:
            # ASSファイルのみ生成
            ass_path = ass_output or f"{os.path.splitext(output_path)[0]}.ass"
            # 解像度を解析
            if isinstance(resolution, tuple):
                resolution_tuple = resolution
            else:
                resolution_tuple = tuple(map(int, resolution.split('x')))
            
            success = engine.generate_subtitle(
                template_name=template_name,
                text=text,
                output_path=ass_path,
                resolution=resolution_tuple,
                **template_params
            )
            
            if success:
                print(f"✅ ASS字幕ファイル生成完了: {ass_path}")
            else:
                print(f"❌ ASS字幕ファイル生成失敗")
                sys.exit(1)
        
        else:
            # 動画生成
            success = engine.generate_video(
                template_name=template_name,
                text=text,
                output_path=output_path,
                ass_path=ass_output,
                resolution=resolution,
                **template_params
            )
            
            if success:
                print(f"✅ 字幕動画生成完了: {output_path}")
                
                # ASSファイルも保存されている場合は表示
                if ass_output:
                    print(f"   ASS字幕ファイル: {ass_output}")
                
            else:
                print(f"❌ 字幕動画生成失敗")
                sys.exit(1)
        
        print(f"🎯 処理完了!")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  処理がユーザーによって中断されました")
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        if '--verbose' in sys.argv or '-v' in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)


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
    
    # 引数からテンプレート固有パラメータを抽出
    for key, value in args.items():
        # CLI引数名をパラメータ名に変換（ハイフンをアンダースコアに）
        param_name = key.replace('-', '_')
        
        if param_name in available_params and param_name not in common_params:
            template_params[param_name] = value
    
    # font_sizeも追加（共通パラメータ）
    if 'font_size' in args:
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