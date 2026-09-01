使用方法
1. 通过 CLI 调用
bash
# 基本用法 - 自动修复全身畸形
python -m markflow.cli.commands execute FixHumanAnatomy image_path="input/girl.jpg"

# 只修复手部
python -m markflow.cli.commands execute FixHumanAnatomy \
    image_path="input/girl.jpg" \
    deformity_type="hands"

# 只修复面部
python -m markflow.cli.commands execute FixHumanAnatomy \
    image_path="input/girl.jpg" \
    deformity_type="face"

# 重度修复（更强效果）
python -m markflow.cli.commands execute FixHumanAnatomy \
    image_path="input/girl.jpg" \
    repair_level="heavy"

# 生成多张候选
python -m markflow.cli.commands execute FixHumanAnatomy \
    image_path="input/girl.jpg" \
    batch=3

# 自定义提示词
python -m markflow.cli.commands execute FixHumanAnatomy \
    image_path="input/girl.jpg" \
    prompt="perfect hands, beautiful face, natural pose" \
    negative="bad anatomy, extra fingers"
2. 直接运行技能文件
bash
# 基本用法
python skills/fix_human_anatomy/skill.py --image_path input/girl.jpg

# 修复手部
python skills/fix_human_anatomy/skill.py --image_path input/girl.jpg --type hands

# 重度修复
python skills/fix_human_anatomy/skill.py --image_path input/girl.jpg --level heavy

# 生成3张候选
python skills/fix_human_anatomy/skill.py --image_path input/girl.jpg --batch 3

# 使用GPU
python skills/fix_human_anatomy/skill.py --image_path input/girl.jpg --device cuda

参数说明
参数	类型	说明	默认值
image_path	string	必填 输入图片路径	-
deformity_type	string	畸形类型: hands/face/body/full	full
repair_level	string	修复强度: light/medium/heavy	medium
output_path	string	输出路径	自动生成
prompt	string	自定义提示词	根据类型自动
negative_prompt	string	自定义负向提示词	根据类型自动
strength	float	重绘强度 (0-1)	根据等级自动
steps	int	迭代步数	根据等级自动
cfg_scale	float	CFG Scale	7.5
seed	int	随机种子	-1
batch	int	生成多张候选	1
device	string	cpu/cuda	cpu
修复等级说明
等级	strength	steps	适用场景
light	0.35	20	轻微瑕疵，微调
medium	0.55	30	一般畸形（推荐）
heavy	0.75	40	严重畸形，大幅重绘
畸形类型说明
类型	修复重点	适用场景
hands	手部结构、手指数量	多指、少指、手指错乱
face	面部对称、五官位置	面部扭曲、不对称
body	身体比例、肢体位置	肢体扭曲、比例失调
full	全身综合修复	多种问题并存