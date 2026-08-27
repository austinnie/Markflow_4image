# scripts/download_controlnet.py
"""
下载 ControlNet 模型（仅下载不需要 mediapipe 的类型）
"""

import os
import sys
from pathlib import Path


def download_controlnet(controlnet_type: str = "canny"):
    """下载指定 ControlNet 模型"""
    model_ids = {
        "canny": "lllyasviel/sd-controlnet-canny",
        "hed": "lllyasviel/sd-controlnet-hed",
        "lineart": "lllyasviel/control_v11p_sd15_lineart",
        "depth": "lllyasviel/sd-controlnet-depth",
        "normal": "lllyasviel/sd-controlnet-normal",
        "mlsd": "lllyasviel/sd-controlnet-mlsd",
        "openpose": "lllyasviel/sd-controlnet-openpose",
    }
    
    if controlnet_type not in model_ids:
        print(f"❌ 不支持的 ControlNet 类型: {controlnet_type}")
        return False
    
    model_id = model_ids[controlnet_type]
    print(f"📦 下载 {controlnet_type} 模型: {model_id}")
    
    try:
        from diffusers import ControlNetModel
        controlnet = ControlNetModel.from_pretrained(model_id)
        print(f"✅ {controlnet_type} 模型下载完成")
        return True
    except ImportError:
        print("❌ diffusers 未安装")
        return False
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False


def main():
    print("=" * 60)
    print("  下载 ControlNet 模型")
    print("=" * 60)
    print()
    print("支持的 ControlNet 类型:")
    print("  - canny    边缘检测 (推荐)")
    print("  - hed      软边缘检测")
    print("  - lineart  线稿提取")
    print("  - depth    深度图")
    print("  - normal   法线图")
    print("  - mlsd     直线检测")
    print("  - openpose 姿态检测 (需要 mediapipe)")
    print()
    
    types = ["canny", "hed", "lineart", "depth", "normal", "mlsd"]
    
    for t in types:
        download_controlnet(t)
        print()


if __name__ == "__main__":
    main()