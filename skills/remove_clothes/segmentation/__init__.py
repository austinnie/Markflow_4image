# skills/remove_clothes/segmentation/__init__.py
"""分割模块 - 支持多种分割方案"""

from .yolo import segment_with_yolo
from .manual import segment_manual
from .clipseg import segment_with_clipseg
from .sam import segment_with_sam
from .grounding_dino import segment_with_grounding_dino

__all__ = [
    'segment_with_yolo',
    'segment_manual',
    'segment_with_clipseg',
    'segment_with_sam',
    'segment_with_grounding_dino',
]