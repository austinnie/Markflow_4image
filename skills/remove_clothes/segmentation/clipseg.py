# skills/remove_clothes/segmentation/clipseg.py
"""CLIPSeg 文字分割 - 根据文字提示分割区域"""

import os
import torch
import numpy as np
from PIL import Image
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# 全局缓存
_model = None
_processor = None


def get_model():
    """懒加载 CLIPSeg 模型"""
    global _model, _processor
    if _model is None:
        try:
            from transformers import CLIPSegProcessor, CLIPSegForImageSegmentation
            
            logger.info("  加载 CLIPSeg 模型...")
            _processor = CLIPSegProcessor.from_pretrained("CIDAS/clipseg-rd64-refined")
            _model = CLIPSegForImageSegmentation.from_pretrained("CIDAS/clipseg-rd64-refined")
            logger.info("  CLIPSeg 模型加载成功")
        except ImportError:
            logger.error("  transformers 未安装，请运行: pip install transformers")
            return None, None
        except Exception as e:
            logger.error(f"  CLIPSeg 模型加载失败: {e}")
            return None, None
    return _model, _processor


def segment_with_clipseg(
    image: Image.Image,
    text: str = "clothes",
    threshold: float = 0.5,
) -> Optional[Image.Image]:
    """
    使用 CLIPSeg 根据文字分割区域
    
    Args:
        image: PIL Image
        text: 分割目标，如 "clothes", "dress", "shirt", "trousers"
        threshold: 分割阈值
    
    Returns:
        遮罩 PIL Image，失败返回 None
    """
    model, processor = get_model()
    if model is None or processor is None:
        return None
    
    try:
        import torch
        
        # 处理输入
        inputs = processor(text=[text], images=image, padding=True, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model(**inputs)
        
        # 转换为遮罩
        mask = torch.sigmoid(outputs.logits).squeeze().numpy()
        mask = (mask > threshold).astype(np.uint8) * 255
        
        # 调整到原图尺寸
        mask_img = Image.fromarray(mask).resize(image.size, Image.Resampling.NEAREST)
        
        # 检查遮罩是否有效
        if np.sum(mask) < 100:
            logger.warning(f"  CLIPSeg 分割区域太小 ({(np.sum(mask)/mask.size)*100:.2f}%)")
            return None
        
        logger.info(f"  CLIPSeg 分割完成，覆盖 {(np.sum(mask)/mask.size)*100:.2f}%")
        return mask_img
        
    except Exception as e:
        logger.error(f"  CLIPSeg 分割失败: {e}")
        return None