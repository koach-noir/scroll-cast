"""
Time Utilities
時間処理関連のユーティリティ
"""


def format_ass_time(seconds: float) -> str:
    """秒数をASS時間フォーマットに変換
    
    Args:
        seconds: 変換する秒数
    
    Returns:
        ASS形式の時間文字列 (H:MM:SS.CC)
    
    Examples:
        >>> format_ass_time(65.5)
        '0:01:05.50'
        >>> format_ass_time(3661.25)
        '1:01:01.25'
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:01d}:{minutes:02d}:{secs:05.2f}"


def seconds_to_ms(seconds: float) -> int:
    """秒をミリ秒に変換
    
    Args:
        seconds: 秒数
        
    Returns:
        ミリ秒
    """
    return int(seconds * 1000)


def ms_to_seconds(milliseconds: int) -> float:
    """ミリ秒を秒に変換
    
    Args:
        milliseconds: ミリ秒
        
    Returns:
        秒数
    """
    return milliseconds / 1000