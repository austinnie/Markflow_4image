# markflow/utils/model_config.py
"""
统一模型配置管理 - 供所有 skills 使用
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List

# ==================== 路径配置 ====================
def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent

PROJECT_ROOT = get_project_root()
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# 模型根目录：我们在 SD_OpenVINO 下
SD_ROOT = PROJECT_ROOT.parent

# ==================== 模型类型配置 ====================
MODEL_TYPES = {
    "sd15": {
        "name": "SD1.5",
        "icon": "🟢",
        "pipeline": "StableDiffusionPipeline",
        "max_resolution": 768,
        "default_steps": 25,
        "dirs": [SD_ROOT / "models" / "sd-v1-5", PROJECT_ROOT / "models" / "sd-v1-5"],
    },
    "sdxl": {
        "name": "SDXL",
        "icon": "🔵",
        "pipeline": "StableDiffusionXLPipeline",
        "max_resolution": 1024,
        "default_steps": 20,
        "dirs": [SD_ROOT / "models" / "sdxl", PROJECT_ROOT / "models" / "sdxl"],
    },
}

LORA_TYPES = {
    "sd15": {
        "name": "SD1.5",
        "icon": "🟢",
        "dirs": [SD_ROOT / "models" / "sd15-lora", PROJECT_ROOT / "models" / "sd15-lora"],
    },
    "sdxl": {
        "name": "SDXL",
        "icon": "🔵",
        "dirs": [SD_ROOT / "models" / "sdxl-lora", PROJECT_ROOT / "models" / "sdxl-lora"],
    },
}

# ==================== 配置 ====================
USER_CONFIG_FILE = PROJECT_ROOT / ".user_config.json"
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_DEFAULT_MODEL = "qwen2.5:1.5b"

def load_user_config() -> Dict[str, Any]:
    if USER_CONFIG_FILE.exists():
        try:
            with open(USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_user_config(data: Dict[str, Any]):
    try:
        with open(USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 保存配置失败: {e}")

_USER_CONFIG = load_user_config()
MODEL_TYPE = _USER_CONFIG.get("model_type", "sd15")
MODEL_SELECTION_MODE = _USER_CONFIG.get("model_selection_mode", "smart")
MANUAL_MODEL_NAME = _USER_CONFIG.get("manual_model_name", None)
USE_OPENVINO = _USER_CONFIG.get("use_openvino", False)
ACTIVE_MODEL_INDEX = _USER_CONFIG.get("active_model_index", 0)
LORA_ACTIVE_INDICES = _USER_CONFIG.get("lora_active_indices", [])
OLLAMA_MODEL = _USER_CONFIG.get("ollama_model", OLLAMA_DEFAULT_MODEL)

# ==================== 扫描与索引 ====================
def scan_models() -> List[Dict]:
    """扫描真实的底模目录，严格区分底模和 LoRA"""
    models = []
    for model_type, config in MODEL_TYPES.items():
        for model_dir in config["dirs"]:
            if model_dir.exists():
                for ext in [".safetensors", ".ckpt", ".pt"]:
                    for f in model_dir.glob(f"*{ext}"):
                        if f.stat().st_size / (1024**3) < 0.5:  # 小于 500MB 忽略
                            continue
                        models.append({
                            "name": f.stem,
                            "filename": f.name,
                            "model_type": model_type,
                            "model_type_name": config["name"],
                            "model_type_icon": config["icon"],
                            "pipeline": config["pipeline"],
                            "max_resolution": config["max_resolution"],
                            "default_steps": config["default_steps"],
                            "path": str(f).replace("\\", "/"),
                            "absolute_path": str(f),
                            "size_gb": round(f.stat().st_size / (1024**3), 2),
                            "tags": ["realistic" if "realistic" in f.stem.lower() else "uncategorized"],
                            "score": 80,
                            "is_ov": False,
                            "ov_path": None,
                        })
    return models

def scan_loras() -> List[Dict]:
    """扫描真实的 LoRA 目录"""
    loras = []
    for lora_type, config in LORA_TYPES.items():
        for lora_dir in config["dirs"]:
            if lora_dir.exists():
                for ext in [".safetensors", ".ckpt", ".pt"]:
                    for f in lora_dir.glob(f"*{ext}"):
                        loras.append({
                            "name": f.stem,
                            "filename": f.name,
                            "lora_type": lora_type,
                            "lora_type_name": config["name"],
                            "lora_type_icon": config["icon"],
                            "path": str(f).replace("\\", "/"),
                            "absolute_path": str(f),
                            "size_mb": round(f.stat().st_size / (1024**2), 2),
                            "tags": ["uncategorized"],
                            "score": 50,
                        })
    return loras

# 自动生成索引
_MODELS = scan_models()
_LORAS = scan_loras()

def get_models() -> List[Dict]:
    return _MODELS

def get_loras() -> List[Dict]:
    return _LORAS

# ==================== 模型路径解析 ====================
def find_model_by_name(model_name: str, models: List[Dict]) -> Optional[Dict]:
    if not model_name:
        return None
    
    for m in models:
        if m.get("name") == model_name or m.get("filename") == model_name:
            return m
    
    filename = Path(model_name).name
    if filename:
        for m in models:
            if m.get("filename") == filename:
                return m

    if Path(model_name).exists():
        abs_path = str(Path(model_name).absolute())
        for m in models:
            if m.get("absolute_path") == abs_path:
                return m
    return None

def resolve_model_path(model_name: str = None) -> Optional[str]:
    available_models = _MODELS
    
    if model_name:
        found = find_model_by_name(model_name, available_models)
        if found:
            return found.get("absolute_path")
        if Path(model_name).exists():
            return str(Path(model_name).absolute())
    
    # 手动模式
    if MODEL_SELECTION_MODE == "manual" and MANUAL_MODEL_NAME:
        found = find_model_by_name(MANUAL_MODEL_NAME, available_models)
        if found:
            return found.get("absolute_path")
    
    # 智能模式
    if MODEL_SELECTION_MODE == "smart" and available_models:
        return available_models[0].get("absolute_path")
    
    # 回退
    if available_models:
        return available_models[0].get("absolute_path")
    
    return None

def resolve_lora_paths(lora_weights: Dict[str, float] = None) -> List[Dict[str, Any]]:
    """
    解析 LoRA 路径
    
    Args:
        lora_weights: LoRA 名称到权重的映射，如 {"lora_000004": 0.7, "aesthetic_anime": 0.9}
    """
    available_loras = _LORAS
    type_loras = [l for l in available_loras if l.get("lora_type") == MODEL_TYPE]
    
    if not type_loras:
        return []
    
    lora_indices = LORA_ACTIVE_INDICES if LORA_ACTIVE_INDICES else [0]
    loras = []
    
    for idx in lora_indices:
        if idx < len(type_loras):
            lora = type_loras[idx]
            lora_name = lora.get("name")
            
            # 如果传入了自定义权重，使用它；否则使用默认 0.8
            weight = 0.8
            if lora_weights and lora_name in lora_weights:
                weight = lora_weights[lora_name]
            
            loras.append({
                "path": lora.get("absolute_path"),
                "weight": weight,
                "name": lora_name,
                "filename": lora.get("filename"),
            })
    return loras

def _check_cuda() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except:
        return False

def get_model_config(model_name: str = None) -> Dict[str, Any]:
    model_path = resolve_model_path(model_name)
    model_display_name = Path(model_path).stem if model_path else MANUAL_MODEL_NAME
    
    model_type_info = {
        "sd15": {"pipeline": "StableDiffusionPipeline", "max_resolution": 768, "default_steps": 25, "default_cfg": 7.5},
        "sdxl": {"pipeline": "StableDiffusionXLPipeline", "max_resolution": 1024, "default_steps": 20, "default_cfg": 7.0},
    }.get(MODEL_TYPE, {})
    
    loras = resolve_lora_paths()
    
    return {
        "model_path": model_path,
        "model_type": MODEL_TYPE,
        "model_name": model_display_name,
        "use_openvino": USE_OPENVINO,
        "device": "cuda" if _check_cuda() and not USE_OPENVINO else "cpu",
        "loras": loras,
        "pipeline": model_type_info.get("pipeline", "StableDiffusionPipeline"),
        "max_resolution": model_type_info.get("max_resolution", 768),
        "default_steps": model_type_info.get("default_steps", 25),
        "default_cfg": model_type_info.get("default_cfg", 7.5),
        "available_models": [m.get("name") for m in _MODELS],
        "available_loras": [l.get("name") for l in _LORAS if l.get("lora_type") == MODEL_TYPE],
        "project_root": str(PROJECT_ROOT),
    }

# ==================== 用户操作 ====================
def update_user_config_item(key: str, value: Any):
    config = load_user_config()
    config[key] = value
    save_user_config(config)
    print(f"✅ 已更新配置: {key} = {value}")

def switch_model(model_type: str = None, model_name: str = None):
    updates = {}
    if model_type:
        updates["model_type"] = model_type
    if model_name:
        updates["manual_model_name"] = model_name
        updates["model_selection_mode"] = "manual"
    
    if updates:
        config = load_user_config()
        config.update(updates)
        save_user_config(config)
        
        global MODEL_TYPE, MANUAL_MODEL_NAME, MODEL_SELECTION_MODE
        MODEL_TYPE = config.get("model_type", "sd15")
        MANUAL_MODEL_NAME = config.get("manual_model_name", None)
        MODEL_SELECTION_MODE = config.get("model_selection_mode", "smart")
        
        print(f"✅ 已切换模型:")
        if model_type:
            print(f"   📊 类型: {model_type}")
        if model_name:
            print(f"   📁 模型: {model_name}")
        
        path = resolve_model_path()
        if path:
            print(f"   📂 路径: {path}")
        return True
    return False

# 在 main() 函数之前添加
def refresh_index():
    """刷新模型和 LoRA 索引（扫描目录并更新全局变量）"""
    global _MODELS, _LORAS
    print("🔄 正在刷新模型索引...")
    _MODELS = scan_models()
    _LORAS = scan_loras()
    print(f"   ✅ 找到 {len(_MODELS)} 个模型, {len(_LORAS)} 个 LoRA")
    return _MODELS, _LORAS
    
# ==================== 命令行入口 ====================
def main():
    parser = argparse.ArgumentParser(description="统一模型配置管理工具")
    parser.add_argument("--status", action="store_true", help="显示当前配置状态")
    parser.add_argument("--type", choices=["sd15", "sdxl"], help="切换模型类型")
    parser.add_argument("--set", type=str, help="设置默认模型")
    parser.add_argument("--list", action="store_true", help="列出所有可用模型")
    parser.add_argument("--list-lora", action="store_true", help="列出所有可用 LoRA")
    parser.add_argument("--ov", action="store_true", help="启用 OpenVINO")
    parser.add_argument("--no-ov", action="store_true", help="禁用 OpenVINO")
    parser.add_argument("--clear", action="store_true", help="清除用户配置")
    parser.add_argument("--refresh", action="store_true", help="刷新模型和 LoRA 索引")  # 新增
    
    args = parser.parse_args()

    if args.refresh:  # 新增
        refresh_index()
        return
        
    if args.status:
        cfg = get_model_config()
        print("\n📊 当前模型配置状态")
        print("=" * 60)
        print(f"  模型类型: {cfg.get('model_type')}")
        print(f"  模型名称: {cfg.get('model_name')}")
        print(f"  模型路径: {cfg.get('model_path')}")
        print(f"  设备: {cfg.get('device')}")
        print(f"  可用模型: {len(cfg.get('available_models', []))} 个")
        print(f"  可用 LoRA: {len(cfg.get('available_loras', []))} 个")
        return
    
    if args.list:
        models = get_models()
        if not models:
            print("❌ 没有找到任何模型")
            return
        print(f"\n📚 可用模型列表 (共 {len(models)} 个):")
        print("=" * 70)
        for i, m in enumerate(models):
            print(f"  [{i:2d}] {m['model_type_icon']} {m['name'][:45]:45s} {m['size_gb']:4.1f}GB")
        return
    
    if args.list_lora:
        loras = get_loras()
        if not loras:
            print("❌ 没有找到任何 LoRA")
            return
        print(f"\n📚 可用 LoRA 列表 (共 {len(loras)} 个):")
        print("=" * 70)
        for i, l in enumerate(loras):
            print(f"  [{i:2d}] {l['lora_type_icon']} {l['name'][:45]:45s} {l['size_mb']:6.1f}MB")
        return
    
    if args.type:
        switch_model(model_type=args.type)
    
    if args.set:
        switch_model(model_name=args.set)
    
    if args.ov:
        update_user_config_item("use_openvino", True)
    
    if args.no_ov:
        update_user_config_item("use_openvino", False)
    
    if args.clear:
        if USER_CONFIG_FILE.exists():
            USER_CONFIG_FILE.unlink()
            print("✅ 已清除用户配置")
        return
    
    parser.print_help()

# ==================== 对外接口 ====================
__all__ = [
    "get_model_config",
    "resolve_model_path",
    "resolve_lora_paths",
    "load_user_config",
    "save_user_config",
    "switch_model",
    "get_models",
    "get_loras",
    "MODEL_TYPE",
    "PROJECT_ROOT",
    "refresh_index",  # 新增
]

if __name__ == "__main__":
    main()