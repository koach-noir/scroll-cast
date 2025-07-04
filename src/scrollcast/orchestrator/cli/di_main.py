"""
Dependency Injection CLI Main
依存性注入パターンを使用したCLIメイン
"""

import sys
import os
import argparse
import time
from typing import Optional

# パッケージのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from subtitle_generator.dependency_injection import get_container, DependencyInjectedTemplateEngine
from subtitle_generator.orchestrator.di_template_engine import DITemplateEngine


def create_parser() -> argparse.ArgumentParser:
    """コマンドライン引数パーサーを作成"""
    parser = argparse.ArgumentParser(
        description='Subtitle Generator with Dependency Injection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate ASS subtitle file
  python di_main.py -i input.txt -t typewriter_fade -o output/

  # Generate video with subtitle
  python di_main.py -i input.txt -t railway_scroll -o output/ --video

  # List available templates
  python di_main.py --list-templates

  # Show template help
  python di_main.py --help-template typewriter_fade
        """
    )
    
    # 入力設定
    parser.add_argument('-i', '--input', type=str,
                       help='Input text file path')
    
    # テンプレート設定
    parser.add_argument('-t', '--template', type=str,
                       help='Template name (e.g., typewriter_fade, railway_scroll)')
    
    # 出力設定
    parser.add_argument('-o', '--output', type=str,
                       help='Output directory path')
    
    # 解像度設定
    parser.add_argument('--width', type=int, default=1080,
                       help='Video width (default: 1080)')
    parser.add_argument('--height', type=int, default=1920,
                       help='Video height (default: 1920)')
    
    # 生成オプション
    parser.add_argument('--video', action='store_true',
                       help='Generate video file')
    parser.add_argument('--ass-only', action='store_true',
                       help='Generate ASS file only')
    
    # 情報表示
    parser.add_argument('--list-templates', action='store_true',
                       help='List available templates')
    parser.add_argument('--help-template', type=str,
                       help='Show help for specific template')
    
    # テンプレートパラメータ（動的に追加される）
    parser.add_argument('--char-interval', type=float,
                       help='Character display interval (typewriter_fade)')
    parser.add_argument('--fade-duration', type=float,
                       help='Fade effect duration (typewriter_fade)')
    parser.add_argument('--pause-between-lines', type=float,
                       help='Pause between lines (typewriter_fade)')
    parser.add_argument('--pause-between-paragraphs', type=float,
                       help='Pause between paragraphs (typewriter_fade)')
    
    parser.add_argument('--fade-in-duration', type=float,
                       help='Fade in duration (railway_scroll)')
    parser.add_argument('--pause-duration', type=float,
                       help='Pause duration (railway_scroll)')
    parser.add_argument('--fade-out-duration', type=float,
                       help='Fade out duration (railway_scroll)')
    parser.add_argument('--overlap-duration', type=float,
                       help='Overlap duration (railway_scroll)')
    parser.add_argument('--empty-line-pause', type=float,
                       help='Empty line pause (railway_scroll)')
    
    # デバッグ・品質
    parser.add_argument('--verbose', action='store_true',
                       help='Verbose output')
    parser.add_argument('--benchmark', action='store_true',
                       help='Show performance benchmark')
    
    return parser


def extract_template_parameters(args: argparse.Namespace) -> dict:
    """コマンドライン引数からテンプレートパラメータを抽出"""
    params = {}
    
    # 共通パラメータ
    param_map = {
        'char_interval': args.char_interval,
        'fade_duration': args.fade_duration,
        'pause_between_lines': args.pause_between_lines,
        'pause_between_paragraphs': args.pause_between_paragraphs,
        'fade_in_duration': args.fade_in_duration,
        'pause_duration': args.pause_duration,
        'fade_out_duration': args.fade_out_duration,
        'overlap_duration': args.overlap_duration,
        'empty_line_pause': args.empty_line_pause,
    }
    
    # None以外の値のみ追加
    for key, value in param_map.items():
        if value is not None:
            params[key] = value
    
    return params


def main():
    """メイン関数"""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # 依存性注入コンテナを取得
        container = get_container()
        template_engine = DITemplateEngine(container)
        
        # 情報表示コマンド
        if args.list_templates:
            print("Available templates:")
            templates = template_engine.list_templates()
            for template_name in sorted(templates):
                print(f"  - {template_name}")
            return 0
        
        if args.help_template:
            template_engine.print_template_help(args.help_template)
            return 0
        
        # 引数検証
        if not args.input:
            print("❌ Error: Input file is required (-i/--input)")
            return 1
        
        if not args.template:
            print("❌ Error: Template is required (-t/--template)")
            return 1
        
        if not args.output:
            print("❌ Error: Output directory is required (-o/--output)")
            return 1
        
        # 入力ファイル読み込み
        if not os.path.exists(args.input):
            print(f"❌ Error: Input file not found: {args.input}")
            return 1
        
        with open(args.input, 'r', encoding='utf-8') as f:
            input_text = f.read()
        
        if args.verbose:
            print(f"✅ Input text loaded: {len(input_text)} characters")
        
        # 解像度設定
        resolution = (args.width, args.height)
        
        # テンプレートパラメータ抽出
        template_params = extract_template_parameters(args)
        
        if args.verbose:
            print(f"✅ Template parameters: {template_params}")
        
        # 生成オプション決定
        generate_video = not args.ass_only
        if args.video:
            generate_video = True
        
        # ベンチマーク開始
        if args.benchmark:
            start_time = time.time()
        
        # 完全なワークフローを実行
        result = template_engine.generate_complete_workflow(
            template_name=args.template,
            input_text=input_text,
            output_dir=args.output,
            resolution=resolution,
            generate_video=generate_video,
            **template_params
        )
        
        # 結果表示
        if result.success:
            print(f"\n🎉 Generation completed successfully!")
            
            if result.ass_output:
                print(f"📄 ASS file: generated successfully")
                print(f"   Size: {len(result.ass_output.content)} bytes")
                print(f"   Lines: {result.ass_output.metadata.line_count}")
            
            if result.video_output:
                print(f"🎬 Video file: {result.video_output.file_path}")
                print(f"   Duration: {result.video_output.duration:.2f}s")
                print(f"   Resolution: {result.video_output.resolution[0]}x{result.video_output.resolution[1]}")
                import os
                if os.path.exists(result.video_output.file_path):
                    size_mb = os.path.getsize(result.video_output.file_path) / (1024 * 1024)
                    print(f"   Size: {size_mb:.2f}MB")
            
            if args.benchmark:
                total_time = time.time() - start_time
                print(f"\n⏱️ Performance:")
                print(f"   Processing time: {result.processing_time:.2f}s")
                print(f"   Total time: {total_time:.2f}s")
                
                if result.ass_output:
                    chars_per_sec = len(input_text) / result.processing_time
                    print(f"   Speed: {chars_per_sec:.0f} chars/second")
            
            return 0
        else:
            print(f"❌ Generation failed: {result.error_message}")
            return 1
    
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())