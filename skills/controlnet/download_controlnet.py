# scripts/download_controlnet.py
"""
下载 ControlNet 模型
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
        "openpose_full": "lllyasviel/control_v11p_sd15_openpose",
        "seg": "lllyasviel/sd-controlnet-seg",           # ⭐ 新增
        "scribble": "lllyasviel/sd-controlnet-scribble", # ⭐ 新增
    }
    
    if controlnet_type not in model_ids:
        print(f"❌ 不支持的 ControlNet 类型: {controlnet_type}")
        print(f"   支持的类型: {', '.join(model_ids.keys())}")
        return False
    
    model_id = model_ids[controlnet_type]
    print(f"📦 下载 {controlnet_type} 模型: {model_id}")
    
    try:
        from diffusers import ControlNetModel
        controlnet = ControlNetModel.from_pretrained(model_id)
        print(f"✅ {controlnet_type} 模型下载完成")
        return True
    except ImportError:
        print("❌ diffusers 未安装，请运行: pip install diffusers")
        return False
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False


def main():
    print("=" * 60)
    print("  下载 ControlNet 模型 (v2.0.0)")
    print("=" * 60)
    print()
    print("支持的 ControlNet 类型:")
    print("  - canny        边缘检测")
    print("  - hed          软边缘检测")
    print("  - lineart      线稿提取")
    print("  - depth        深度图")
    print("  - normal       法线图")
    print("  - mlsd         直线检测")
    print("  - openpose     姿态检测")
    print("  - openpose_full 完整姿态 (含手/脸)")
    print("  - seg          语义分割 ⭐ 新增")
    print("  - scribble     涂鸦控制 ⭐ 新增")
    print()
    
    # 默认下载全部（除了 openpose_full 较大）
    types = ["canny", "hed", "lineart", "depth", "normal", "mlsd", "openpose", "seg", "scribble"]
    
    print("📥 开始下载所有模型...")
    print()
    
    success = 0
    for t in types:
        if download_controlnet(t):
            success += 1
        print()
    
    print("=" * 60)
    print(f"✅ 下载完成: {success}/{len(types)} 个模型")
    print("=" * 60)


if __name__ == "__main__":
    main()