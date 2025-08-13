"""
厚東川監視システム - スタイル統合モジュール
全てのCSSスタイルを統合して提供
"""

from .core_styles import get_core_styles
from .component_styles import get_component_styles  
from .responsive_styles import get_responsive_styles

def get_all_styles() -> str:
    """統合されたアプリケーションスタイルを取得
    
    Returns:
        str: 全てのCSSスタイルを統合したHTML文字列
    """
    return f"""<style>
{get_core_styles()}
{get_component_styles()}
{get_responsive_styles()}
</style>"""

__all__ = [
    'get_all_styles',
    'get_core_styles', 
    'get_component_styles',
    'get_responsive_styles'
]