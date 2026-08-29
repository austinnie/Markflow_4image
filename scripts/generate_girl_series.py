# scripts/generate_girl_series.py
"""
给 input/girl.jpg 批量生成系列图
自动组合不同的背景、姿势、表情、服装等技能
"""

import sys
import time
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from markflow.cli.commands import execute_skill

# ==================== 配置 ====================
REFERENCE_IMAGE = "input/girl.jpg"  # 你的统一输入目录
OUTPUT_ROOT = Path("output")        # 统一输出目录
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

# 批量任务列表：每个任务包含（技能名称，参数）
GENERATION_TASKS = [
    # ========== 1. 换背景系列 ==========
    {"skill": "change_background", "params": {"preset": "beach", "strength": 0.55}},
    {"skill": "change_background", "params": {"preset": "forest", "strength": 0.55}},
    {"skill": "change_background", "params": {"preset": "city", "strength": 0.55}},
    {"skill": "change_background", "params": {"preset": "sakura", "strength": 0.55}},
    {"skill": "change_background", "params": {"preset": "sunset", "strength": 0.55}},

    # ========== 2. 换衣服系列 ==========
    {"skill": "change_clothes", "params": {"prompt": "wearing a beautiful elegant black evening gown", "strength": 0.65}},
    {"skill": "change_clothes", "params": {"prompt": "wearing a white summer dress", "strength": 0.65}},
    {"skill": "change_clothes", "params": {"prompt": "wearing a casual red jacket and jeans", "strength": 0.65}},

    # ========== 3. 换表情系列 ==========
    {"skill": "change_expression", "params": {"expression": "smile", "strength": 0.45}},
    {"skill": "change_expression", "params": {"expression": "laughing", "strength": 0.45}},
    {"skill": "change_expression", "params": {"expression": "surprised", "strength": 0.45}},

    # ========== 4. 换发色/发型系列 ==========
    {"skill": "change_hair", "params": {"hair_color": "pink", "strength": 0.45}},
    {"skill": "change_hair", "params": {"hair_color": "blonde", "strength": 0.45}},

    # ========== 5. 加配饰/特效 ==========
    {"skill": "add_glasses", "params": {"style": "round", "strength": 0.35}},
    {"skill": "add_animal_ears", "params": {"animal": "cat", "strength": 0.55}},

    # ========== 6. 多技能复杂组合（换背景+换姿态） ==========
    {"skill": "expand_to_full_body", "params": {"prompt": "a beautiful elegant woman standing, full body", "controlnet_type": "openpose"}},
    {"skill": "style_transfer", "params": {"style": "oil_painting", "strength": 0.75}},
    {"skill": "style_transfer", "params": {"style": "watercolor", "strength": 0.75}},

    # ========== 7. 二次元/写实转换 ==========
    {"skill": "anime_to_real", "params": {"style": "photorealistic", "strength": 0.8}},
]


def main():
    print(f"📸 准备为 {REFERENCE_IMAGE} 生成 {len(GENERATION_TASKS)} 张系列图...")
    print(f"💾 输出目录: {OUTPUT_ROOT}")

    success_count = 0

    for idx, task in enumerate(GENERATION_TASKS, 1):
        skill_name = task['skill']
        params = task['params']

        # 自动生成输出文件名
        safe_name = f"{idx:02d}_{skill_name.replace('_', '-')}"
        output_path = str(OUTPUT_ROOT / f"{safe_name}.png")

        # 统一注入参数
        params['image_path'] = REFERENCE_IMAGE
        params['output_path'] = output_path

        print(f"\n[{idx}/{len(GENERATION_TASKS)}] 🚀 正在调用: {skill_name}")
        print(f"    📝 参数: {params}")

        try:
            result = execute_skill(skill_name, **params)

            if isinstance(result, dict) and result.get('status') == 'success':
                print(f"    ✅ 成功! 保存至: {result.get('output_path')}")
                success_count += 1
            else:
                # 打印错误详情
                if isinstance(result, dict):
                    print(f"    ❌ 失败: {result.get('error', '未知错误')}")
                else:
                    print(f"    ❌ 失败: {result}")

        except Exception as e:
            print(f"    ❌ 执行异常: {e}")
            import traceback
            traceback.print_exc()

        # 等待一下防止连续调用太吃内存
        time.sleep(1)

    print(f"\n🎉 批量生成结束！成功 {success_count}/{len(GENERATION_TASKS)} 张。")
    print(f"📂 所有生成的图片已保存在: {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()