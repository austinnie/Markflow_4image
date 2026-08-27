# skills/remove_clothes/segmentation/manual.py
"""手动绘制遮罩 - 鼠标交互"""

import numpy as np
import cv2
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def segment_manual(image: Image.Image, brush_size: int = 30) -> Image.Image:
    """
    手动绘制遮罩（鼠标交互）

    Args:
        image: PIL Image
        brush_size: 初始画笔大小

    Returns:
        遮罩 PIL Image
    """
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    h, w = img_cv.shape[:2]

    overlay = np.zeros((h, w, 3), dtype=np.uint8)
    mask = np.zeros((h, w), dtype=np.uint8)
    drawing = False
    brush_size_current = brush_size

    print("\n" + "=" * 50)
    print("  手动绘制遮罩模式")
    print("=" * 50)
    print("  🖱️  按住鼠标左键绘制遮罩（白色区域）")
    print("  🔄  滚轮调节画笔大小")
    print("  ⌨️  按 R 键重置遮罩")
    print("  ⌨️  按 Q 或 空格键 完成绘制")
    print("=" * 50 + "\n")

    def draw_callback(event, x, y, flags, param):
        nonlocal drawing, brush_size_current
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            cv2.circle(mask, (x, y), brush_size_current, 255, -1)
            cv2.circle(overlay, (x, y), brush_size_current, (0, 255, 0), -1)
        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                cv2.circle(mask, (x, y), brush_size_current, 255, -1)
                cv2.circle(overlay, (x, y), brush_size_current, (0, 255, 0), -1)
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
        elif event == cv2.EVENT_MOUSEWHEEL:
            delta = flags
            brush_size_current = min(100, max(5, brush_size_current + (5 if delta > 0 else -5)))
            print(f"    画笔大小: {brush_size_current}")

    cv2.namedWindow('Draw Mask - Remove Clothes')
    cv2.setMouseCallback('Draw Mask - Remove Clothes', draw_callback)

    while True:
        display = img_cv.copy()
        mask_overlay = cv2.addWeighted(display, 0.5, overlay, 0.5, 0)

        cv2.putText(mask_overlay, f"Brush: {brush_size_current}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(mask_overlay, "Draw clothes, press Q to finish", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow('Draw Mask - Remove Clothes', mask_overlay)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q') or key == 32:
            break
        elif key == ord('r'):
            mask = np.zeros((h, w), dtype=np.uint8)
            overlay = np.zeros((h, w, 3), dtype=np.uint8)
            print("  🔄 遮罩已重置")

    cv2.destroyAllWindows()

    if np.sum(mask > 0) < 100:
        print("  ⚠️ 遮罩区域太小，使用椭圆默认遮罩")
        mask = np.zeros((h, w), dtype=np.uint8)
        cx, cy = w // 2, h // 2
        cv2.ellipse(mask, (cx, cy), (w // 4, h // 3), 0, 0, 360, 255, -1)

    mask = cv2.GaussianBlur(mask, (21, 21), 0)
    print(f"  ✅ 遮罩完成，覆盖 {np.sum(mask > 0)} 像素")
    return Image.fromarray(mask, mode="L")