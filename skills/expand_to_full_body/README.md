cd E:\SD_OpenVINO\Markflow_4image

# 基础用法
python -m skills.expand_to_full_body.skill --input photo.jpg

# 自定义提示词
python -m skills.expand_to_full_body.skill --input photo.jpg --prompt "a beautiful woman, elegant, stylish dress"

# 使用 ControlNet
python -m skills.expand_to_full_body.skill --input photo.jpg --controlnet-type openpose

# 强制扩展（即使已是全身图）
python -m skills.expand_to_full_body.skill --input photo.jpg --force-expand

# 指定目标尺寸
python -m skills.expand_to_full_body.skill --input photo.jpg --width 768 --height 1024

# 高质量输出
python -m skills.expand_to_full_body.skill --input photo.jpg --steps 40 --strength 0.7

# 完整参数
python -m skills.expand_to_full_body.skill --input photo.jpg --output output/full.png --prompt "a beautiful woman, wearing red dress, elegant" --controlnet-type openpose --steps 35 --strength 0.65 --width 768 --height 1024