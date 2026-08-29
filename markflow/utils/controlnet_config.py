# markflow/utils/controlnet_config.py
"""
ControlNet 专用配置管理器 (本地离线版)
"""
import os
from pathlib import Path
from typing import Optional

# 获取系统环境变量，如果没有设置则回退到默认路径
CONTROLNET_ROOT = os.getenv("CONTROLNET_ROOT", r"E:\SD_OpenVINO")

CONTROLNET_AUX_DIR = Path(CONTROLNET_ROOT) / "hf_cache" / ".cache" / "controlnet_aux"
CONTROLNET_MODEL_DIR = Path(CONTROLNET_ROOT) / "models" / "controlnet"

# 强制离线环境，禁止尝试联网下载
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# 预处理器映射
PREPROCESSOR_MAP = {
    "HED": CONTROLNET_AUX_DIR / "ControlNetHED.pth",
    "MLSD": CONTROLNET_AUX_DIR / "mlsd_large_512_fp32.pth",
    "OPENPOSE": CONTROLNET_AUX_DIR / "body_pose_model.pth",
    "DEPTH": CONTROLNET_AUX_DIR / "dpt_hybrid-midas-501f0c75.pt",
}

# ControlNet 底层模型映射 (对应你的 models/controlnet 文件夹)
CONTROLNET_MODEL_MAP = {
    "canny": "models--lllyasviel--sd-controlnet-canny",
    "lineart": "models--lllyasviel--control_v11p_sd15_lineart",
    "openpose": "models--lllyasviel--control_v11p_sd15_openpose",
    "depth": "models--lllyasviel--sd-controlnet-depth",
    "mlsd": "models--lllyasviel--sd-controlnet-mlsd",
    "hed": "models--lllyasviel--sd-controlnet-hed",
}

def resolve_controlnet_path(model_key: str) -> Optional[str]:
    """解析底层 ControlNet 模型路径"""
    folder_name = CONTROLNET_MODEL_MAP.get(model_key)
    if not folder_name:
        return None
    
    # 1. 检查是否在 E:\SD_OpenVINO\models\controlnet 目录下
    target_dir = CONTROLNET_MODEL_DIR / folder_name
    if target_dir.exists():
        # 2. 因为 HuggingFace 缓存通常带 snapshots，需要找一下里面真正的模型文件夹
        # 优先检查目录下有没有 config.json
        if (target_dir / "config.json").exists():
            return str(target_dir)
        
        # 如果目录下没有 config.json，说明是 HF 的缓存结构，进入 snapshots 里找
        if (target_dir / "snapshots").exists():
            # 遍历 snapshots 下的文件夹，找到包含 config.json 的那个
            for snapshot in (target_dir / "snapshots").iterdir():
                if (snapshot / "config.json").exists():
                    return str(snapshot)
    
    # 3. 如果上述都没找到，返回 None，并打印详细日志
    print(f"❌ 警告：未找到本地 ControlNet 模型 {folder_name}，请检查目录结构。")
    return None