# skills/remove_clothes/segmentation/grounding_dino.py
"""Grounding DINO 文字检测分割"""

import os
import numpy as np
from PIL import Image, ImageDraw
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

# 全局缓存
_model = None


def get_model():
    """懒加载 Grounding DINO 模型"""
    global _model
    
    if _model is not None:
        return _model
    
    try:
        from groundingdino.util.inference import load_model, load_image, predict
        
        # 模型路径
        model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
        config_path = os.path.join(model_dir, "groundingdino_swint_ogc.py")
        checkpoint_path = os.path.join(model_dir, "groundingdino_swint_ogc.pth")
        
        # 如果模型不存在，提示下载
        if not os.path.exists(config_path) or not os.path.exists(checkpoint_path):
            logger.warning("  Grounding DINO 模型不存在")
            logger.warning(f"  请下载到: {model_dir}/")
            logger.warning("  下载地址: https://github.com/IDEA-Research/GroundingDINO")
            return None
        
        logger.info("  加载 Grounding DINO 模型...")
        _model = load_model(config_path, checkpoint_path)
        logger.info("  Grounding DINO 模型加载成功")
        return _model
        
    except ImportError:
        logger.error("  groundingdino 未安装")
        logger.error("  请运行: pip install groundingdino-py")
        return None
    except Exception as e:
        logger.error(f"  Grounding DINO 加载失败: {e}")
        return None


def segment_with_grounding_dino(
    image: Image.Image,
    text: str = "clothes",
    box_threshold: float = 0.25,
    text_threshold: float = 0.25,
) -> Optional[Image.Image]:
    """
    使用 Grounding DINO 检测并分割
    
    Args:
        image: PIL Image
        text: 检测目标，如 "clothes", "dress", "shirt"
        box_threshold: 检测阈值
        text_threshold: 文字匹配阈值
    
    Returns:
        遮罩 PIL Image，失败返回 None
    """
    model = get_model()
    if model is None:
        return None
    
    try:
        from groundingdino.util.inference import load_image, predict
        
        # 保存临时文件
        temp_path = "temp_grounding.jpg"
        image.save(temp_path)
        
        # 检测
        image_source, image_pil = load_image(temp_path)
        boxes, logits, phrases = predict(
            model=model,
            image=image_pil,
            caption=text,
            box_threshold=box_threshold,
            text_threshold=text_threshold,
        )
        
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        if len(boxes) == 0:
            logger.warning(f"  Grounding DINO 未检测到: {text}")
            return None
        
        # 生成遮罩（将所有框合并）
        h, w = image.size[1], image.size[0]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        for box in boxes:
            x1, y1, x2, y2 = box
            x1, y1, x2, y2 = int(x1 * w), int(y1 * h), int(x2 * w), int(y2 * h)
            mask[y1:y2, x1:x2] = 255
        
        # 膨胀使边缘更平滑
        import cv2
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)
        
        mask_img = Image.fromarray(mask)
        logger.info(f"  Grounding DINO 检测到 {len(boxes)} 个 {text} 区域")
        return mask_img
        
    except Exception as e:
        logger.error(f"  Grounding DINO 分割失败: {e}")
        return None