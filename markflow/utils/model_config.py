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
    """获取项目根目录"""
    return Path(__file__).parent.parent.parent

PROJECT_ROOT = get_project_root()
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# 默认模型目录（相对于项目根目录）
DEFAULT_MODEL_DIRS = {
    "sd15": PROJECT_ROOT / "../models/sd-v1-5",
    "sdxl": PROJECT_ROOT / "../models/sdxl",
}

DEFAULT_LORA_DIRS = {
    "sd15": PROJECT_ROOT / "../models/sd15-lora",
    "sdxl": PROJECT_ROOT / "../models/sdxl-lora",
}

# ==================== Ollama 配置 ====================
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_DEFAULT_MODEL = "qwen2.5:1.5b"

# ==================== 用户配置 ====================
USER_CONFIG_FILE = PROJECT_ROOT / ".user_config.json"

def load_user_config() -> Dict[str, Any]:
    """加载用户配置"""
    if USER_CONFIG_FILE.exists():
        try:
            with open(USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_user_config(data: Dict[str, Any]):
    """保存用户配置"""
    try:
        with open(USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 保存配置失败: {e}")

# ==================== 加载索引 ====================
def load_index(index_name: str) -> Dict:
    """加载索引文件"""
    index_file = SCRIPTS_DIR / index_name
    if not index_file.exists():
        return {"models": [], "loras": [], "default": None}
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"models": [], "loras": [], "default": None}

MODEL_INDEX = load_index("models_index.json")
LORA_INDEX = load_index("lora_index.json")

# ==================== 读取用户配置 ====================
_USER_CONFIG = load_user_config()

MODEL_TYPE = _USER_CONFIG.get("model_type", "sd15")
MODEL_SELECTION_MODE = _USER_CONFIG.get("model_selection_mode", "smart")
MANUAL_MODEL_NAME = _USER_CONFIG.get("manual_model_name", None)
USE_OPENVINO = _USER_CONFIG.get("use_openvino", False)
ACTIVE_MODEL_INDEX = _USER_CONFIG.get("active_model_index", 0)
LORA_ACTIVE_INDICES = _USER_CONFIG.get("lora_active_indices", [])

# Ollama 配置（必须在 _USER_CONFIG 定义之后）
OLLAMA_MODEL = _USER_CONFIG.get("ollama_model", OLLAMA_DEFAULT_MODEL)

# ==================== 路径解析核心函数 ====================

def resolve_path_from_entry(entry: Dict, index_type: str = "model") -> Optional[str]:
    """从索引条目解析路径"""
    if entry.get("absolute_path"):
        abs_path = Path(entry["absolute_path"])
        if abs_path.exists():
            return str(abs_path.absolute())
    
    if entry.get("path"):
        abs_path = PROJECT_ROOT / entry["path"]
        if abs_path.exists():
            return str(abs_path.absolute())
    
    if entry.get("filename"):
        if index_type == "model":
            dirs = MODEL_INDEX.get("model_dirs_relative", {})
        else:
            dirs = LORA_INDEX.get("lora_dirs_relative", {})
        
        entry_type = entry.get("model_type") or entry.get("lora_type", "sd15")
        if entry_type in dirs:
            rel_dir = dirs[entry_type]
            if not Path(rel_dir).is_absolute():
                abs_path = PROJECT_ROOT / rel_dir / entry["filename"]
            else:
                abs_path = Path(rel_dir) / entry["filename"]
            if abs_path.exists():
                return str(abs_path.absolute())
    
    return None

def find_model_by_name(model_name: str, models: List[Dict]) -> Optional[Dict]:
    """
    精确查找模型
    优先精确匹配 name 或 filename
    """
    if not model_name:
        return None
    
    # 1. 精确匹配 name
    for m in models:
        if m.get("name") == model_name:
            return m
    
    # 2. 精确匹配 filename
    for m in models:
        if m.get("filename") == model_name:
            return m
    
    # 3. 如果 model_name 包含路径，提取文件名匹配
    filename = Path(model_name).name
    if filename:
        for m in models:
            if m.get("filename") == filename:
                return m
    
    # 4. 检查是否是完整路径
    if Path(model_name).exists():
        abs_path = str(Path(model_name).absolute())
        for m in models:
            if m.get("absolute_path") == abs_path:
                return m
            if m.get("path") and str(PROJECT_ROOT / m.get("path")) == abs_path:
                return m
    
    return None

def resolve_model_path(model_name: str = None) -> Optional[str]:
    """解析模型路径"""
    available_models = MODEL_INDEX.get("models", [])
    
    # 1. 手动指定模型名 - 精确匹配
    if model_name:
        found = find_model_by_name(model_name, available_models)
        if found:
            return resolve_path_from_entry(found, "model")
        # 如果是文件路径，直接检查
        if Path(model_name).exists():
            return str(Path(model_name).absolute())
        # 尝试在默认目录中查找
        for model_type, dir_path in DEFAULT_MODEL_DIRS.items():
            test_path = dir_path / model_name
            if test_path.exists():
                return str(test_path.absolute())
            for ext in ['.safetensors', '.ckpt', '.pth']:
                if not model_name.endswith(ext):
                    test_path = dir_path / (model_name + ext)
                    if test_path.exists():
                        return str(test_path.absolute())
        # 如果找不到，打印警告并继续使用默认
        print(f"⚠️ 未找到模型: {model_name}")
    
    # 2. 手动模式 - 使用 MANUAL_MODEL_NAME
    if MODEL_SELECTION_MODE == "manual" and MANUAL_MODEL_NAME:
        found = find_model_by_name(MANUAL_MODEL_NAME, available_models)
        if found:
            path = resolve_path_from_entry(found, "model")
            if path:
                return path
        print(f"⚠️ 手动模式未找到模型: {MANUAL_MODEL_NAME}")
    
    # 3. 智能模式 - 使用索引默认
    if MODEL_SELECTION_MODE == "smart":
        default_name = MODEL_INDEX.get("default")
        if default_name:
            found = find_model_by_name(default_name, available_models)
            if found:
                return resolve_path_from_entry(found, "model")
    
    # 4. Legacy 模式
    if MODEL_SELECTION_MODE == "legacy":
        legacy_mapping = MODEL_INDEX.get("legacy_mapping", {}).get(MODEL_TYPE, {})
        if str(ACTIVE_MODEL_INDEX) in legacy_mapping:
            filename = legacy_mapping[str(ACTIVE_MODEL_INDEX)]
            model_dirs = MODEL_INDEX.get("model_dirs_relative", {})
            if MODEL_TYPE in model_dirs:
                rel_dir = model_dirs[MODEL_TYPE]
                if not Path(rel_dir).is_absolute():
                    test_path = PROJECT_ROOT / rel_dir / filename
                else:
                    test_path = Path(rel_dir) / filename
                if test_path.exists():
                    return str(test_path.absolute())
    
    # 5. 回退 - 第一个可用模型
    if available_models:
        first = available_models[0]
        path = resolve_path_from_entry(first, "model")
        if path:
            return path
    
    # 6. 默认目录查找
    for model_type, dir_path in DEFAULT_MODEL_DIRS.items():
        if dir_path.exists():
            for ext in ['.safetensors', '.ckpt', '.pth']:
                files = list(dir_path.glob(f"*{ext}"))
                if files:
                    return str(files[0].absolute())
    
    return None

def find_lora_by_name(lora_name: str, loras: List[Dict]) -> Optional[Dict]:
    """精确查找 LoRA"""
    if not lora_name:
        return None
    
    for l in loras:
        if l.get("name") == lora_name:
            return l
        if l.get("filename") == lora_name:
            return l
    
    return None

def resolve_lora_paths() -> List[Dict[str, Any]]:
    """解析 LoRA 路径列表"""
    loras = []
    available_loras = LORA_INDEX.get("loras", [])
    type_loras = [l for l in available_loras if l.get("lora_type") == MODEL_TYPE]
    
    if not type_loras:
        return loras
    
    # ✅ 使用 _USER_CONFIG 读取
    lora_indices = _USER_CONFIG.get("lora_active_indices", [])
    if not lora_indices:
        lora_indices = [0]
    
    for idx in lora_indices:
        if idx < len(type_loras):
            lora = type_loras[idx]
            path = resolve_path_from_entry(lora, "lora")
            if path:
                loras.append({
                    "path": path,
                    "weight": 0.8,
                    "name": lora.get("name", f"lora_{idx}"),
                    "filename": lora.get("filename", ""),
                })
    
    return loras

def _check_cuda() -> bool:
    """检查 CUDA 是否可用"""
    try:
        import torch
        return torch.cuda.is_available()
    except:
        return False

def get_model_config(model_name: str = None) -> Dict[str, Any]:
    """
    获取完整的模型配置 - 始终返回字典
    """
    model_path = resolve_model_path(model_name)
    
    # 获取模型名称（用于显示）
    model_display_name = None
    if model_path:
        # 从路径中提取文件名
        model_display_name = Path(model_path).stem
    if not model_display_name:
        model_display_name = MANUAL_MODEL_NAME or MODEL_INDEX.get("default")
    
    model_type_info = {
        "sd15": {
            "pipeline": "StableDiffusionPipeline",
            "max_resolution": 768,
            "default_steps": 25,
            "default_cfg": 7.5,
        },
        "sdxl": {
            "pipeline": "StableDiffusionXLPipeline",
            "max_resolution": 1024,
            "default_steps": 20,
            "default_cfg": 7.0,
        }
    }.get(MODEL_TYPE, {})
    
    model_dirs = MODEL_INDEX.get("model_dirs_relative", {})
    lora_dirs = LORA_INDEX.get("lora_dirs_relative", {})
    loras = resolve_lora_paths()
    
    # ✅ 始终返回字典
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
        "model_dirs": model_dirs,
        "lora_dirs": lora_dirs,
        "project_root": str(PROJECT_ROOT),
        "available_models": [m.get("name") for m in MODEL_INDEX.get("models", [])],
        "available_loras": [l.get("name") for l in LORA_INDEX.get("loras", []) if l.get("lora_type") == MODEL_TYPE],
    }

def update_user_config_item(key: str, value: Any):
    """更新单个配置项"""
    config = load_user_config()
    config[key] = value
    save_user_config(config)
    print(f"✅ 已更新配置: {key} = {value}")

def switch_model(model_type: str = None, model_name: str = None):
    """切换模型"""
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
        
        # 重新加载全局变量
        global MODEL_TYPE, MANUAL_MODEL_NAME, MODEL_SELECTION_MODE
        MODEL_TYPE = config.get("model_type", "sd15")
        MANUAL_MODEL_NAME = config.get("manual_model_name", None)
        MODEL_SELECTION_MODE = config.get("model_selection_mode", "smart")
        
        print(f"✅ 已切换模型:")
        if model_type:
            print(f"   📊 类型: {model_type}")
        if model_name:
            print(f"   📁 模型: {model_name}")
        
        # 显示解析后的路径
        path = resolve_model_path()
        if path:
            print(f"   📂 路径: {path}")
        return True
    return False

# ==================== Ollama 函数 ====================

def get_ollama_config() -> Dict[str, Any]:
    """获取 Ollama 配置"""
    config = load_user_config()
    return {
        "model": config.get("ollama_model", OLLAMA_DEFAULT_MODEL),
        "host": OLLAMA_HOST,
        "temperature": config.get("ollama_temperature", 0.7),
        "max_tokens": config.get("ollama_max_tokens", 200),
    }

def set_ollama_model(model_name: str) -> bool:
    """切换 Ollama 模型"""
    config = load_user_config()
    config["ollama_model"] = model_name
    save_user_config(config)
    
    global OLLAMA_MODEL
    OLLAMA_MODEL = model_name
    
    print(f"✅ 已切换到 Ollama 模型: {model_name}")
    return True

def list_ollama_models() -> List[str]:
    """列出已安装的 Ollama 模型"""
    try:
        import requests
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        if response.status_code == 200:
            data = response.json()
            return [m.get("name") for m in data.get("models", [])]
        return []
    except:
        return []

def show_ollama_status():
    """显示 Ollama 状态"""
    config = load_user_config()
    ollama_model = config.get("ollama_model", OLLAMA_DEFAULT_MODEL)
    
    print("\n" + "=" * 50)
    print("📊 Ollama 配置状态")
    print("=" * 50)
    print(f"  当前模型: {ollama_model}")
    print(f"  Host: {OLLAMA_HOST}")
    print(f"  Temperature: {config.get('ollama_temperature', 0.7)}")
    print(f"  Max Tokens: {config.get('ollama_max_tokens', 200)}")
    
    models = list_ollama_models()
    if models:
        print(f"\n📦 已安装的 Ollama 模型 ({len(models)} 个):")
        for m in models:
            mark = " 👈 当前" if m == ollama_model else ""
            print(f"  - {m}{mark}")
    else:
        print("\n⚠️ 无法连接到 Ollama 或没有安装模型")
        print("   请确保 Ollama 正在运行: ollama serve")

# ==================== 显示状态 ====================

def show_status():
    """显示当前配置状态"""
    cfg = get_model_config()
    user_config = load_user_config()
    
    print("\n" + "=" * 70)
    print("📊 当前模型配置状态")
    print("=" * 70)
    print(f"\n📁 配置文件: {USER_CONFIG_FILE}")
    print(f"   {'存在' if USER_CONFIG_FILE.exists() else '不存在（使用默认）'}")
    
    print(f"\n📦 模型配置:")
    print(f"  模型类型: {cfg.get('model_type', '未设置')}")
    print(f"  模型路径: {cfg.get('model_path', '未找到')}")
    print(f"  模型名称: {cfg.get('model_name', '未设置')}")
    print(f"  选择模式: {user_config.get('model_selection_mode', 'smart')}")
    
    print(f"\n💻 运行环境:")
    print(f"  设备: {cfg.get('device', 'cpu')}")
    print(f"  OpenVINO: {'✅ 启用' if cfg.get('use_openvino') else '❌ 禁用'}")
    print(f"  项目根目录: {cfg.get('project_root', '未知')}")
    
    print(f"\n📁 模型目录 (相对路径):")
    for mt, rel_path in cfg.get('model_dirs', {}).items():
        print(f"  {mt}: {rel_path}")
    
    print(f"\n📁 LoRA 目录 (相对路径):")
    for lt, rel_path in cfg.get('lora_dirs', {}).items():
        print(f"  {lt}: {rel_path}")
    
    print(f"\n⚙️  生成参数:")
    print(f"  默认步数: {cfg.get('default_steps', 25)}")
    print(f"  默认 CFG: {cfg.get('default_cfg', 7.5)}")
    print(f"  最大分辨率: {cfg.get('max_resolution', 768)}")
    print(f"  Pipeline: {cfg.get('pipeline', 'StableDiffusionPipeline')}")
    
    print(f"\n📦 LoRA ({len(cfg.get('loras', []))} 个激活):")
    if cfg.get('loras'):
        for lora in cfg.get('loras', []):
            print(f"  - {lora.get('name', 'unknown')}: {lora.get('path', '')}")
    else:
        print("  (无)")
    
    print(f"\n🤖 Ollama 配置:")
    print(f"  模型: {user_config.get('ollama_model', OLLAMA_DEFAULT_MODEL)}")
    print(f"  Host: {OLLAMA_HOST}")
    
    print(f"\n📚 可用模型 ({len(cfg.get('available_models', []))} 个):")
    for name in cfg.get('available_models', [])[:5]:
        print(f"  - {name}")
    if len(cfg.get('available_models', [])) > 5:
        print(f"  ... 还有 {len(cfg.get('available_models', [])) - 5} 个")

# ==================== 命令行入口 ====================

def main():
    parser = argparse.ArgumentParser(
        description="统一模型配置管理工具",
        epilog="""
示例:
  python markflow/utils/model_config.py --status           # 查看当前配置
  python markflow/utils/model_config.py --type sdxl        # 切换到 SDXL
  python markflow/utils/model_config.py --set aiiiiii01_v10 # 设置默认模型
  python markflow/utils/model_config.py --list             # 列出所有可用模型
  python markflow/utils/model_config.py --list-lora        # 列出所有 LoRA
  python markflow/utils/model_config.py --lora 0           # 激活索引 0 的 LoRA
  python markflow/utils/model_config.py --ov               # 启用 OpenVINO
  python markflow/utils/model_config.py --ollama qwen2.5:1.5b  # 切换 Ollama 模型
  python markflow/utils/model_config.py --ollama-status    # 查看 Ollama 状态
  python markflow/utils/model_config.py --ollama-list      # 列出已安装的 Ollama 模型
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--status", action="store_true", help="显示当前配置状态")
    parser.add_argument("--type", choices=["sd15", "sdxl"], help="切换模型类型 (SD1.5 / SDXL)")
    parser.add_argument("--set", type=str, help="设置默认模型（模型名称）")
    parser.add_argument("--list", action="store_true", help="列出所有可用模型")
    parser.add_argument("--list-lora", action="store_true", help="列出所有可用 LoRA")
    parser.add_argument("--lora", type=int, nargs="+", help="激活指定索引的 LoRA")
    parser.add_argument("--ov", action="store_true", help="启用 OpenVINO")
    parser.add_argument("--no-ov", action="store_true", help="禁用 OpenVINO")
    parser.add_argument("--clear", action="store_true", help="清除用户配置（恢复默认）")
    
    parser.add_argument("--ollama", type=str, help="切换 Ollama 模型")
    parser.add_argument("--ollama-status", action="store_true", help="查看 Ollama 状态")
    parser.add_argument("--ollama-list", action="store_true", help="列出已安装的 Ollama 模型")
    
    args = parser.parse_args()
    
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    if args.clear:
        if USER_CONFIG_FILE.exists():
            USER_CONFIG_FILE.unlink()
            print("✅ 已清除用户配置，恢复默认")
        else:
            print("ℹ️ 没有用户配置需要清除")
        return
    
    if args.list:
        models = MODEL_INDEX.get("models", [])
        if not models:
            print("❌ 没有找到任何模型")
            return
        print(f"\n📚 可用模型列表 (共 {len(models)} 个):")
        print("=" * 70)
        for i, m in enumerate(models):
            icon = m.get("model_type_icon", "📁")
            type_name = m.get("model_type_name", "")
            size = m.get("size_gb", 0)
            stars = "⭐" * (m.get("score", 0) // 20)
            print(f"  [{i:2d}] {icon} {m['name'][:45]:45s} {size:4.1f}GB  {stars}")
            print(f"        类型: {type_name} | 标签: {', '.join(m.get('tags', []))}")
        return
    
    if args.list_lora:
        loras = LORA_INDEX.get("loras", [])
        if not loras:
            print("❌ 没有找到任何 LoRA")
            return
        print(f"\n📚 可用 LoRA 列表 (共 {len(loras)} 个):")
        print("=" * 70)
        for i, l in enumerate(loras):
            icon = l.get("lora_type_icon", "📁")
            type_name = l.get("lora_type_name", "")
            size = l.get("size_mb", 0)
            stars = "⭐" * (l.get("score", 0) // 20)
            active = " 👈 激活" if i in _USER_CONFIG.get("lora_active_indices", []) else ""
            print(f"  [{i:2d}] {icon} {l['name'][:45]:45s} {size:6.1f}MB  {stars}{active}")
            print(f"        类型: {type_name} | 标签: {', '.join(l.get('tags', []))}")
        return
    
    if args.type:
        switch_model(model_type=args.type)
    
    if args.set:
        switch_model(model_name=args.set)
    
    if args.lora is not None:
        config = load_user_config()
        config["lora_active_indices"] = args.lora
        save_user_config(config)
        print(f"✅ 已激活 LoRA 索引: {args.lora}")
    
    if args.ov:
        update_user_config_item("use_openvino", True)
    if args.no_ov:
        update_user_config_item("use_openvino", False)
    
    if args.ollama:
        set_ollama_model(args.ollama)
    
    if args.ollama_status:
        show_ollama_status()
        return
    
    if args.ollama_list:
        models = list_ollama_models()
        if models:
            print(f"\n📦 已安装的 Ollama 模型 ({len(models)} 个):")
            for m in models:
                print(f"  - {m}")
        else:
            print("❌ 无法获取 Ollama 模型列表")
            print("   请确保 Ollama 正在运行: ollama serve")
        return
    
    if args.status or args.type or args.set:
        show_status()

# ==================== 对外接口 ====================
__all__ = [
    "get_model_config",
    "resolve_model_path",
    "resolve_lora_paths",
    "load_user_config",
    "save_user_config",
    "update_user_config_item",
    "switch_model",
    "get_ollama_config",
    "set_ollama_model",
    "list_ollama_models",
    "show_ollama_status",
    "MODEL_TYPE",
    "PROJECT_ROOT",
    "OLLAMA_MODEL",
    "OLLAMA_HOST",
]

if __name__ == "__main__":
    main()