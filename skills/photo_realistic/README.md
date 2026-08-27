# 默认：什么都不做
python -m markflow.cli.commands execute photo_realistic image_path="test.jpg"

# 只加噪点
python -m markflow.cli.commands execute photo_realistic image_path="test.jpg" enable_noise=True

# 只加暗角
python -m markflow.cli.commands execute photo_realistic image_path="test.jpg" enable_vignette=True

# 只注入 EXIF
python -m markflow.cli.commands execute photo_realistic image_path="test.jpg" enable_exif=True

# 全部开启
python -m markflow.cli.commands execute photo_realistic image_path="test.jpg" enable_noise=True enable_vignette=True enable_sharpen=True enable_exif=True

# 指定相机和强度
python -m markflow.cli.commands execute photo_realistic image_path="test.jpg" enable_exif=True camera="canon_r5" strength="strong"

# 直接运行
python skills/photo_realistic/skill.py --input test.jpg --noise --vignette --exif