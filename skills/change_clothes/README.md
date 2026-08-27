# 换衣服 - 默认连衣裙
python -m markflow.cli.commands execute change_clothes image_path="skills/change_clothes/output/test1.jpg"

# 换衣服 - 指定具体款式
python -m markflow.cli.commands execute change_clothes image_path="skills/change_clothes/output/test1.jpg" prompt="wearing a red leather jacket, black jeans, cool style"

# 换衣服 - 自定义参数
python -m markflow.cli.commands execute change_clothes image_path="skills/change_clothes/output/test1.jpg" prompt="wearing a white wedding dress, elegant" strength=0.7 steps=30

# 批量换衣服
python skills/change_clothes/skill.py --input ./images/ --batch -o skills/change_clothes/output/ --prompt "wearing a summer dress, floral pattern"


🚀 Change Clothes 完整命令
基础用法
bash
python -m skills.change_clothes.skill --input skills/remove_clothes/female-hat5.jpg --output output/changed_default.png
1. 自定义服装样式（修改提示词）
bash
python -m skills.change_clothes.skill --input skills/remove_clothes/female-hat5.jpg --output output/changed_dress.png --prompt "wearing a beautiful red evening gown, elegant, luxurious, detailed folds, masterpiece, best quality"
bash
python -m skills.change_clothes.skill --input skills/remove_clothes/female-hat5.jpg --output output/changed_suit.png --prompt "wearing a professional blue suit, formal, business attire, detailed, high quality"
bash
python -m skills.change_clothes.skill --input skills/remove_clothes/female-hat5.jpg --output output/changed_hanfu.png --prompt "wearing traditional Chinese Hanfu, flowing silk, embroidered, elegant, masterpiece"
bash
python -m skills.change_clothes.skill --input skills/remove_clothes/female-hat5.jpg --output output/changed_wedding.png --prompt "wearing a beautiful white wedding dress, lace details, elegant, romantic, masterpiece"
bash
python -m skills.change_clothes.skill --input skills/remove_clothes/female-hat5.jpg --output output/changed_casual.png --prompt "wearing a casual white T-shirt and jeans, comfortable, modern, high quality"
2. 手动绘制遮罩（精确控制）
bash
python -m skills.change_clothes.skill --input skills/remove_clothes/female-hat5.jpg --output output/changed_manual.png --manual-mask
bash
python -m skills.change_clothes.skill --input skills/remove_clothes/female-hat5.jpg --output output/changed_manual_dress.png --manual-mask --prompt "wearing a beautiful black dress, elegant, fashion, masterpiece"
3. 启用 ControlNet（保持姿态）
bash
python -m skills.change_clothes.skill --input skills/remove_clothes/female-hat5.jpg --output output/changed_controlnet.png --controlnet-type openpose
bash
python -m skills.change_clothes.skill --input skills/remove_clothes/female-hat5.jpg --output output/changed_controlnet_canny.png --controlnet-type canny --prompt "wearing a red jacket, stylish, modern"
4. 调整生成参数（质量/速度）
bash
# 高质量（更多步数）
python -m skills.change_clothes.skill --input skills/remove_clothes/female-hat5.jpg --output output/changed_hq.png --steps 35 --strength 0.7

# 快速生成（更少步数）
python -m skills.change_clothes.skill --input skills/remove_clothes/female-hat5.jpg --output output/changed_fast.png --steps 15 --strength 0.5

# 固定随机种子（可复现结果）
python -m skills.change_clothes.skill --input skills/remove_clothes/female-hat5.jpg --output output/changed_seed.png --seed 42
5. 保存遮罩（调试用）
bash
python -m skills.change_clothes.skill --input skills/remove_clothes/female-hat5.jpg --output output/changed_mask.png --save-mask
6. 禁用 ControlNet（仅 Inpaint）
bash
python -m skills.change_clothes.skill --input skills/remove_clothes/female-hat5.jpg --output output/changed_no_control.png --no-controlnet
7. 组合使用（最佳效果推荐）
bash
# 推荐：手动遮罩 + ControlNet + 高质量
python -m skills.change_clothes.skill --input skills/remove_clothes/female-hat5.jpg --output output/changed_best.png --manual-mask --controlnet-type openpose --steps 35 --strength 0.7 --prompt "wearing a beautiful red evening gown, elegant, luxurious, masterpiece, best quality"

8. 批量处理
bash
# 批量处理目录下所有图片
python -m skills.change_clothes.skill --input skills/remove_clothes/ --batch --output output/batch_changed/
bash
# 批量 + 指定服装
python -m skills.change_clothes.skill --input skills/remove_clothes/ --batch --output output/batch_dress/ --prompt "wearing a beautiful blue dress, elegant"


## 📊 命令速查表

| 场景 | 命令 |
|------|------|
| **基础** | `--input photo.jpg --output out.png` |
| **自定义服装** | `--prompt "wearing a red dress"` |
| **手动遮罩** | `--manual-mask` |
| **ControlNet** | `--controlnet-type openpose` |
| **高质量** | `--steps 35 --strength 0.7` |
| **固定种子** | `--seed 42` |
| **批量处理** | `--input ./images/ --batch` |
| **保存遮罩** | `--save-mask` |
| **禁用 ControlNet** | `--no-controlnet` |
