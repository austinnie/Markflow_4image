# 换衣服 - 默认连衣裙
python -m markflow.cli.commands execute change_clothes image_path="skills/change_clothes/output/test1.jpg"

# 换衣服 - 指定具体款式
python -m markflow.cli.commands execute change_clothes image_path="skills/change_clothes/output/test1.jpg" prompt="wearing a red leather jacket, black jeans, cool style"

# 换衣服 - 自定义参数
python -m markflow.cli.commands execute change_clothes image_path="skills/change_clothes/output/test1.jpg" prompt="wearing a white wedding dress, elegant" strength=0.7 steps=30

# 批量换衣服
python skills/change_clothes/skill.py --input ./images/ --batch -o skills/change_clothes/output/ --prompt "wearing a summer dress, floral pattern"