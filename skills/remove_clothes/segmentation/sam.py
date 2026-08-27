# skills/remove_clothes/segmentation/sam.py
"""SAM (Segment Anything) 点击分割"""

import os
import numpy as np
from PIL import Image
from typing import Optional, Tuple, List
import logging
import torch

logger = logging.getLogger(__name__)

# 全局缓存
_predictor = None


def get_predictor(model_type: str = "vit_b", checkpoint: str = None):
    """懒加载 SAM 模型"""
    global _predictor
    
    if _predictor is not None:
        return _predictor
    
    try:
        from segment_anything import sam_model_registry, SamPredictor
        
        # 自动下载 checkpoint
        if checkpoint is None:
            # 默认使用 vit_b 模型
            checkpoint = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "models",
                "sam_vit_b_01ec64.pth"
            )
            
            # 如果模型不存在，提示下载
            if not os.path.exists(checkpoint):
                logger.warning(f"  SAM 模型不存在: {checkpoint}")
                logger.warning("  请下载 sam_vit_b_01ec64.pth 到 models/ 目录")
                logger.warning("  下载地址: https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth")
                return None
        
        logger.info(f"  加载 SAM 模型: {checkpoint}")
        sam = sam_model_registry[model_type](checkpoint=checkpoint)
        _predictor = SamPredictor(sam)
        logger.info("  SAM 模型加载成功")
        return _predictor
        
    except ImportError:
        logger.error("  segment-anything 未安装，请运行: pip install segment-anything")
        return None
    except Exception as e:
        logger.error(f"  SAM 模型加载失败: {e}")
        return None


def segment_with_sam(
    image: Image.Image,
    points: List[Tuple[int, int]],
    labels: List[int] = None,
    mode: str = "click",
) -> Optional[Image.Image]:
    """
    使用 SAM 分割区域
    
    Args:
        image: PIL Image
        points: 点击坐标列表 [(x, y), ...]
        labels: 标签列表 [1, 0, ...] (1=前景, 0=背景)
        mode: "click" 点击模式 | "box" 框选模式
    
    Returns:
        遮罩 PIL Image，失败返回 None
    """
    predictor = get_predictor()
    if predictor is None:
        return None
    
    try:
        # 设置图片
        predictor.set_image(np.array(image))
        
        if labels is None:
            labels = [1] * len(points)
        
        # 转换为 numpy
        input_points = np.array(points)
        input_labels = np.array(labels)
        
        # 预测
        masks, scores, logits = predictor.predict(
            point_coords=input_points,
            point_labels=input_labels,
            multimask_output=True,
        )
        
        # 取得分最高的 mask
        best_idx = np.argmax(scores)
        mask = (masks[best_idx] * 255).astype(np.uint8)
        
        # 检查遮罩是否有效
        if np.sum(mask) < 100:
            logger.warning("  SAM 分割区域太小")
            return None
        
        mask_img = Image.fromarray(mask)
        logger.info(f"  SAM 分割完成，覆盖 {(np.sum(mask)/mask.size)*100:.2f}%")
        return mask_img
        
    except Exception as e:
        logger.error(f"  SAM 分割失败: {e}")
        return None


def get_points_from_click(image: Image.Image) -> Optional[List[Tuple[int, int]]]:
    """
    交互式点击获取点
    
    Args:
        image: PIL Image
    
    Returns:
        点击坐标列表
    """
    import cv2
    
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    points = []
    
    print("\n" + "=" * 50)
    print("  SAM 点击分割模式")
    print("=" * 50)
    print("  在衣服上点击左键选择点")
    print("  在背景上点击右键排除点")
    print("  按 Q 完成")
    print("=" * 50 + "\n")
    
    def click_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((x, y, 1))
            cv2.circle(img_cv, (x, y), 5, (0, 255, 0), -1)
            print(f"  添加前景点: ({x}, {y})")
        elif event == cv2.EVENT_RBUTTONDOWN:
            points.append((x, y, 0))
            cv2.circle(img_cv, (x, y), 5, (0, 0, 255), -1)
            print(f"  添加背景点: ({x}, {y})")
    
    cv2.namedWindow('SAM Click Segmentation')
    cv2.setMouseCallback('SAM Click Segmentation', click_callback)
    
    while True:
        cv2.imshow('SAM Click Segmentation', img_cv)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 32:
            break
    
    cv2.destroyAllWindows()
    
    if not points:
        return None
    
    return [(x, y) for x, y, _ in points], [label for _, _, label in points]