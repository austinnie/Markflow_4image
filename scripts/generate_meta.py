import json
from pathlib import Path

SKILLS_DIR = Path("skills")

# ============================================================
# 通用参数定义（所有技能都支持）
# ============================================================
COMMON_INPUTS = [
    {"name": "image_path", "type": "string", "required": True, "description": "输入图片路径"},
    {"name": "prompt", "type": "string", "required": False, "description": "自定义提示词"},
    {"name": "negative_prompt", "type": "string", "required": False, "description": "负向提示词", "default": ""},
    {"name": "strength", "type": "float", "required": False, "description": "重绘强度 (0-1)", "default": 0.6},
    {"name": "steps", "type": "integer", "required": False, "description": "迭代步数", "default": 25},
    {"name": "cfg_scale", "type": "float", "required": False, "description": "提示词引导强度", "default": 7.5},
    {"name": "seed", "type": "integer", "required": False, "description": "随机种子，-1 表示随机", "default": -1},
    {"name": "model_name", "type": "string", "required": False, "description": "底模名称 (如: sd-v1-5-tiny)"},
    {"name": "width", "type": "integer", "required": False, "description": "输出宽度"},
    {"name": "height", "type": "integer", "required": False, "description": "输出高度"},
    {"name": "output_path", "type": "string", "required": False, "description": "输出路径"},
    {"name": "output_dir", "type": "string", "required": False, "description": "输出目录"},
    {"name": "controlnet_type", "type": "string", "required": False, "description": "ControlNet 类型 (canny, openpose, depth, hed, mlsd, lineart)", "default": "canny"},
    {"name": "device", "type": "string", "required": False, "description": "设备 (cpu/cuda)", "default": "cpu"},
]

# ============================================================
# 每个技能的独有参数（必填/可选）
# ============================================================
SKILL_SPECIFIC_INPUTS = {
    # ---- 基础编辑 ----
    "change_expression": [
        {"name": "expression", "type": "string", "required": True, "description": "表情 (smile, laugh, surprised, sad, angry, crying, etc.)"}
    ],
    "change_eye_color": [
        {"name": "color", "type": "string", "required": True, "description": "眼睛颜色 (blue, green, brown, hazel, red, purple, etc.)"}
    ],
    "change_age": [
        {"name": "age", "type": "string", "required": True, "description": "年龄 (young, old, child, teenager, middle-aged, elderly)"}
    ],
    "change_gender": [
        {"name": "direction", "type": "string", "required": True, "description": "性别转换方向 (male_to_female, female_to_male)"}
    ],
    "change_skin_tone": [
        {"name": "tone", "type": "string", "required": True, "description": "肤色 (light, tan, dark, pale, olive, ebony)"}
    ],
    "change_nationality": [
        {"name": "ethnicity", "type": "string", "required": True, "description": "种族特征 (caucasian, asian, african, hispanic, middle_eastern, indian)"}
    ],
    "change_hair": [
        {"name": "hair_color", "type": "string", "required": False, "description": "发色 (blonde, pink, red, black, brown, blue, etc.)"},
        {"name": "hairstyle", "type": "string", "required": False, "description": "发型 (short, long, curly, straight, wavy, ponytail, bun, etc.)"}
    ],
    "change_clothing_style": [
        {"name": "style", "type": "string", "required": True, "description": "服装风格 (futuristic, vintage, casual, formal, sporty, bohemian, gothic, etc.)"}
    ],
    "change_lighting": [
        {"name": "lighting", "type": "string", "required": True, "description": "光照模式 (golden_hour, night, studio, soft, dramatic, warm, cool, etc.)"}
    ],
    "change_makeup": [
        {"name": "style", "type": "string", "required": True, "description": "妆容风格 (natural, glamour, heavy, artistic, no_makeup, etc.)"}
    ],
    "change_furniture": [
        {"name": "style", "type": "string", "required": True, "description": "家具风格 (scandinavian, modern, traditional, minimalist, industrial, rustic, etc.)"}
    ],
    "change_perspective": [
        {"name": "perspective", "type": "string", "required": True, "description": "视角 (aerial, low_angle, high_angle, close_up, wide, worm_eye, bird_eye)"}
    ],
    "change_body_type": [
        {"name": "body_type", "type": "string", "required": True, "description": "体型 (slim, muscular, curvy, athletic, plus_size, etc.)"}
    ],
    "change_face": [
        {"name": "face_prompt", "type": "string", "required": True, "description": "面部描述 (beautiful face, natural smile, perfect skin, etc.)"}
    ],
    
    # ---- 转移/转换 ----
    "day_night_transfer": [
        {"name": "mode", "type": "string", "required": True, "description": "转换模式 (day_to_night, night_to_day)"}
    ],
    "season_transfer": [
        {"name": "season", "type": "string", "required": True, "description": "季节 (spring, summer, autumn, winter)"}
    ],
    "weather_transfer": [
        {"name": "weather", "type": "string", "required": True, "description": "天气 (sunny, rainy, snowy, cloudy, foggy, stormy, windy)"}
    ],
    "style_transfer": [
        {"name": "style", "type": "string", "required": True, "description": "风格 (watercolor, oil_painting, anime, sketch, realistic, cinematic, etc.)"}
    ],
    
    # ---- 风格转换 ----
    "anime_to_real": [
        {"name": "style", "type": "string", "required": False, "description": "写实风格 (photorealistic, cinematic, studio, vintage, etc.)"}
    ],
    "real_to_anime": [
        {"name": "style", "type": "string", "required": False, "description": "动漫风格 (modern, classic, ghibli, shinkai, makoto, etc.)"}
    ],
    "colorize_sketch": [
        {"name": "style", "type": "string", "required": False, "description": "上色风格 (anime, realistic, watercolor, vibrant, soft, etc.)"}
    ],
    "sketch_to_real": [
        {"name": "style", "type": "string", "required": False, "description": "写实风格 (photorealistic, cinematic, studio, etc.)"}
    ],
    "old_photo_restore": [
        {"name": "style", "type": "string", "required": False, "description": "修复风格 (vibrant, natural, enhanced, vintage_preserve, etc.)"}
    ],
    
    # ---- 添加/替换 ----
    "add_glasses": [
        {"name": "style", "type": "string", "required": True, "description": "眼镜款式 (round, square, aviator, cat_eye, oval, rectangle, rimless)"}
    ],
    "add_tattoo": [
        {"name": "tattoo", "type": "string", "required": True, "description": "纹身图案 (dragon, flower, star, tribal, skull, feather, geometric, etc.)"}
    ],
    "add_background_objects": [
        {"name": "object", "type": "string", "required": True, "description": "背景物体 (flowers, trees, clouds, birds, butterflies, stars, etc.)"}
    ],
    "remove_object": [
        {"name": "skip_manual", "type": "boolean", "required": False, "description": "跳过手动遮罩，自动识别", "default": False}
    ],
    "replace_object": [
        {"name": "object_prompt", "type": "string", "required": True, "description": "替换后的物体描述"},
        {"name": "skip_manual", "type": "boolean", "required": False, "description": "跳过手动遮罩，自动识别", "default": False}
    ],
    
    # ---- 生成类 ----
    "fantasy_character": [
        {"name": "fantasy_type", "type": "string", "required": True, "description": "幻想角色类型 (elf, dwarf, orc, fairy, dragonborn, angel, demon, etc.)"}
    ],
    "mecha_generator": [
        {"name": "style", "type": "string", "required": False, "description": "机甲风格 (realistic, anime, cyberpunk, military, sleek, etc.)"}
    ],
    "human_to_robot": [
        {"name": "style", "type": "string", "required": False, "description": "机器人风格 (cyberpunk, retro, sleek, military, android, etc.)"}
    ],
    
    # ---- 换背景（使用 preset） ----
    "change_background": [
        {"name": "preset", "type": "string", "required": True, "description": "背景预设 (beach, forest, city, sakura, sunset, snow, rain, night, garden, mountain, studio, cyberpunk)"}
    ],
}

# ============================================================
# 技能描述
# ============================================================
SKILL_DESCRIPTIONS = {
    "add_background_objects": "添加背景物体 (花朵、树木、云朵等)",
    "add_glasses": "添加眼镜",
    "add_tattoo": "添加纹身",
    "anime_to_real": "动漫风格转写实风格",
    "change_age": "改变人物年龄",
    "change_background": "替换图片背景 (预设场景)",
    "change_body_type": "改变人物体型",
    "change_clothing_style": "改变服装风格",
    "change_expression": "改变人物表情",
    "change_eye_color": "改变眼睛颜色",
    "change_face": "换脸/面部重绘",
    "change_furniture": "改变室内家具风格",
    "change_gender": "改变人物性别",
    "change_hair": "改变发型/发色",
    "change_lighting": "改变光照效果",
    "change_makeup": "改变妆容",
    "change_nationality": "改变种族特征",
    "change_perspective": "改变视角",
    "change_skin_tone": "改变肤色",
    "colorize_sketch": "线稿上色",
    "day_night_transfer": "昼夜转换",
    "fantasy_character": "幻想角色生成",
    "human_to_robot": "人转机器人",
    "mecha_generator": "机甲角色生成",
    "old_photo_restore": "老照片修复",
    "real_to_anime": "写实转动漫风格",
    "remove_object": "移除图片中的物体",
    "replace_object": "替换图片中的物体",
    "season_transfer": "季节转换",
    "sketch_to_real": "素描转写实",
    "style_transfer": "风格转换 (水彩/油画/动漫等)",
    "weather_transfer": "天气转换",
}

# ============================================================
# 生成函数
# ============================================================
def generate_meta(skill_name: str):
    """生成单个 meta.json"""
    skill_dir = SKILLS_DIR / skill_name
    meta_file = skill_dir / "meta.json"
    
    if meta_file.exists():
        print(f"⏭️  {skill_name} 已有 meta.json，跳过")
        return
    
    if not skill_dir.exists():
        print(f"❌ {skill_name} 目录不存在")
        return
    
    description = SKILL_DESCRIPTIONS.get(skill_name, f"{skill_name} 技能")
    
    # 构建输入参数
    inputs = []
    
    # 1. 添加 image_path（必填）
    inputs.append({"name": "image_path", "type": "string", "required": True, "description": "输入图片路径"})
    
    # 2. 添加技能特有参数（必填的排在前面）
    specific = SKILL_SPECIFIC_INPUTS.get(skill_name, [])
    for inp in specific:
        inputs.append(inp)
    
    # 3. 添加 prompt（可选，除了 change_face 已经有 face_prompt）
    if skill_name != "change_face":
        inputs.append({"name": "prompt", "type": "string", "required": False, "description": "自定义提示词"})
    
    # 4. 添加通用参数
    common = [
        {"name": "negative_prompt", "type": "string", "required": False, "description": "负向提示词", "default": ""},
        {"name": "strength", "type": "float", "required": False, "description": "重绘强度 (0-1)", "default": 0.6},
        {"name": "steps", "type": "integer", "required": False, "description": "迭代步数", "default": 25},
        {"name": "cfg_scale", "type": "float", "required": False, "description": "提示词引导强度", "default": 7.5},
        {"name": "seed", "type": "integer", "required": False, "description": "随机种子，-1 表示随机", "default": -1},
        {"name": "model_name", "type": "string", "required": False, "description": "底模名称"},
        {"name": "width", "type": "integer", "required": False, "description": "输出宽度"},
        {"name": "height", "type": "integer", "required": False, "description": "输出高度"},
        {"name": "output_path", "type": "string", "required": False, "description": "输出路径"},
        {"name": "controlnet_type", "type": "string", "required": False, "description": "ControlNet 类型", "default": "canny"},
        {"name": "device", "type": "string", "required": False, "description": "设备 (cpu/cuda)", "default": "cpu"},
    ]
    inputs.extend(common)
    
    # 判断 controlnet_type 默认值
    for inp in inputs:
        if inp["name"] == "controlnet_type":
            if any(k in skill_name for k in ["change", "add", "face", "hair", "eye", "skin", "clothing"]):
                inp["default"] = "openpose"
            else:
                inp["default"] = "canny"
    
    meta = {
        "name": skill_name,
        "display_name": skill_name.replace("_", " ").title(),
        "description": description,
        "version": "1.0.0",
        "inputs": inputs,
        "outputs": [
            {"name": "status", "description": "执行状态 (success/error)"},
            {"name": "output_path", "description": "输出图片路径"},
            {"name": "image_paths", "description": "所有生成的图片路径列表"}
        ],
        "dependencies": [],
        "tags": ["image", "edit", "controlnet"],
        "config": {
            "device": "cpu",
            "default_steps": 25,
            "default_cfg": 7.5,
            "default_strength": 0.6,
            "controlnet_type": "openpose" if any(k in skill_name for k in ["change", "add", "face", "hair", "eye", "skin", "clothing"]) else "canny"
        }
    }
    
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {skill_name}/meta.json 已生成 ({len(inputs)} 个参数)")

def main():
    print("=" * 60)
    print("📦 批量生成 meta.json (完整参数版)")
    print("=" * 60)
    
    for skill_name in SKILL_DESCRIPTIONS:
        generate_meta(skill_name)
    
    print("=" * 60)
    print("✅ 完成!")

if __name__ == "__main__":
    main()