"""
CSS統合モジュール - Kotogawa監視システム
統一されたスタイル管理を提供
"""

from .core_styles import get_core_styles
from .component_styles import get_component_styles
from .responsive_styles import get_responsive_styles

__all__ = [
    'get_core_styles',
    'get_component_styles',
    'get_responsive_styles',
    'get_all_styles'
]


def get_all_styles() -> str:
    """
    すべてのスタイルを統合して返す
    
    Returns:
        str: 統合されたCSSスタイル文字列
    """
    return f"""
    <style>
        {get_core_styles()}
        {get_component_styles()}
        {get_responsive_styles()}
    </style>
    """