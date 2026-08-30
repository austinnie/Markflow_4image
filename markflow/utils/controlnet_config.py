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
    """解析底层 ControlNet 模型路径（增强版）"""
    folder_name = CONTROLNET_MODEL_MAP.get(model_key)
    if not folder_name:
        return None
    
    # 1. 检查是否在 E:\SD_OpenVINO\models\controlnet 目录下
    target_dir = CONTROLNET_MODEL_DIR / folder_name
    
    # 2. 如果是 HF 缓存结构，找 snapshots
    if target_dir.exists():
        # 检查是否直接有 config.json
        if (target_dir / "config.json").exists():
            return str(target_dir)
        
        # 检查 snapshots 子目录
        snapshots_dir = target_dir / "snapshots"
        if snapshots_dir.exists():
            for snapshot in snapshots_dir.iterdir():
                if snapshot.is_dir() and (snapshot / "config.json").exists():
                    return str(snapshot)
        
        # 3. 尝试任何子目录中的 config.json
        for subdir in target_dir.iterdir():
            if subdir.is_dir() and (subdir / "config.json").exists():
                return str(subdir)
    
    # 4. 回退：如果传入的是完整路径，直接检查
    if model_key and Path(model_key).exists():
        return str(model_key)
    
    # 5. 打印详细警告
    print(f"❌ 警告：未找到本地 ControlNet 模型 {folder_name}")
    print(f"   查找路径: {target_dir}")
    print(f"   💡 请检查 models/controlnet/ 目录结构")
    return None