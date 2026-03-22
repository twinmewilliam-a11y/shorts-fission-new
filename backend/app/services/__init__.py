# backend/app/services/__init__.py
from .downloader import VideoDownloader, AccountMonitor
from .variant_engine import VariantEngine, PIPVariantEngineV4, AudioVariantEngine
from .subtitle_service import SubtitleService
from .text_variant_service import TextVariantEngine, SpintaxEngine
from .text_layer_engine_v2 import (
    TextLayerEngineV2,
    generate_text_layer,
    get_available_effects,
    get_available_scenes,
)
from .effect_templates import (
    EFFECT_TEMPLATES,
    SCENE_CONFIG,
    POSITION_GRID,
    get_random_effects,
)
from .word_level_animation import (
    WordLevelAnimationEngine,
    generate_word_level_animation,
    get_available_templates as get_word_animation_templates,
    get_available_positions as get_word_animation_positions,
)
from .subtitle_extractor import (
    extract_subtitle,
    extract_word_timestamps,
)

__all__ = [
    'VideoDownloader',
    'AccountMonitor',
    'VariantEngine',
    'PIPVariantEngineV4',
    'AudioVariantEngine',
    'SubtitleService',
    'TextVariantEngine',
    'SpintaxEngine',
    'TextLayerEngineV2',
    'generate_text_layer',
    'get_available_effects',
    'get_available_scenes',
    'EFFECT_TEMPLATES',
    'SCENE_CONFIG',
    'POSITION_GRID',
    'get_random_effects',
    # Word Level Animation (v3.0)
    'WordLevelAnimationEngine',
    'generate_word_level_animation',
    'get_word_animation_templates',
    'get_word_animation_positions',
    # Subtitle Extractor
    'extract_subtitle',
    'extract_word_timestamps',
]
