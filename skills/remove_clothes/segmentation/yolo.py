# skills/remove_clothes/segmentation/yolo.py
"""YOLO 人体分割 - 自动检测人体躯干区域"""

import os
import numpy as np
import cv2
from PIL import Image
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# 全局缓存
_yolo_model = None
YOLO_AVAILABLE = False

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    logger.warning("YOLO 未安装")


def get_yolo_model():
    """懒加载 YOLO 模型"""
    global _yolo_model
    if not YOLO_AVAILABLE:
        return None

    if _yolo_model is None:
        try:
            _yolo_model = YOLO("yolov8n-seg.pt")
            logger.info("  YOLO 模型加载成功")
        except Exception as e:
            logger.warning(f"  YOLO 模型加载失败: {e}")
            _yolo_model = False
    return _yolo_model


def segment_with_yolo(
    image: Image.Image,
    neck_ratio: float = 0.18,
    hip_ratio: float = 0.65,
    expand_ratio: float = 0.08,
) -> Optional[Image.Image]:
    """
    使用 YOLO 检测人体并提取躯干区域

    Args:
        image: PIL Image
        neck_ratio: 脖子位置（从头顶往下比例）
        hip_ratio: 臀部位置（从头顶往下比例）
        expand_ratio: 左右扩展比例

    Returns:
        遮罩 PIL Image，失败返回 None
    """
    h, w = image.size[1], image.size[0]

    yolo = get_yolo_model()
    if not yolo:
        return None

    try:
        results = yolo(image, verbose=False)
        if len(results) == 0 or results[0].masks is None:
            logger.warning("  YOLO 未检测到人体")
            return None

        masks = results[0].masks.data.cpu().numpy()
        combined = np.zeros((h, w), dtype=np.uint8)
        for m in masks:
            m_resized = cv2.resize(m, (w, h))
            combined = np.maximum(combined, (m_resized > 0.5).astype(np.uint8) * 255)

        coords = np.where(combined > 0)
        if len(coords[0]) == 0:
            logger.warning("  YOLO 未检测到有效遮罩")
            return None

        y_min, y_max = coords[0].min(), coords[0].max()
        body_h = y_max - y_min

        # 躯干范围：脖子到臀部
        neck = y_min + int(body_h * neck_ratio)
        hip = y_min + int(body_h * hip_ratio)

        x_min, x_max = coords[1].min(), coords[1].max()
        body_w = x_max - x_min
        left = x_min + int(body_w * expand_ratio)
        right = x_max - int(body_w * expand_ratio)

        clothes = np.zeros_like(combined)
        clothes[neck:hip, left:right] = combined[neck:hip, left:right]

        # 平滑边缘
        kernel = np.ones((5, 5), np.uint8)
        clothes = cv2.dilate(clothes, kernel, iterations=1)
        clothes = cv2.GaussianBlur(clothes, (9, 9), 0)

        if np.sum(clothes > 0) < 100:
            logger.warning("  YOLO 遮罩区域太小")
            return None

        logger.info(f"  YOLO 分割完成，覆盖 {np.sum(clothes > 0)} 像素")
        return Image.fromarray(clothes, mode="L")

    except Exception as e:
        logger.warning(f"  YOLO 分割失败: {e}")
        return None