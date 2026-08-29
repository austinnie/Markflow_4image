# test_change_clothes.py
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入技能
from skills.change_clothes.skill import ChangeClothes

if __name__ == "__main__":
    # 设置你的绝对路径（请替换为你真实的图片路径）
    input_image = r"E:\SD_OpenVINO\Markflow_4image\skills\controlnet_img2img\test.jpg"
    
    # 实例化技能
    skill = ChangeClothes(config={'device': 'cpu'})  # CPU模式
    
    print("\n" + "="*50)
    print("开始执行 change_clothes...")
    print("="*50)
    
    # 直接调用 execute
    result = skill.execute(
        image_path=input_image,                     # 必填
        prompt="wearing a beautiful white lace dress", 
        controlnet_type="openpose",                 # 提取姿态
        use_controlnet=True,                        # 启用保形引擎
        save_mask=False                             # 不保存遮罩
    )
    
    print("\n" + "="*50)
    print("执行结果:")
    print("="*50)
    print(result)