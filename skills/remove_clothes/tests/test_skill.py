"""
Remove Clothes Skill 单元测试
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from skills.remove_clothes_skill.skill import RemoveClothesSkill


class TestRemoveClothesSkill(unittest.TestCase):
    """
    RemoveClothesSkill 测试类
    """

    def setUp(self):
        """测试前准备"""
        self.skill = RemoveClothesSkill()

    def test_execute_with_valid_params(self):
        """测试正常执行"""
        result = self.skill.execute(--input="", --output='自动生成', --model='`zenityXmix.inpainting.safetensors`', --prompt='见默认提示词', --negative='见默认负面词', --steps='25', --strength='0.5', --seed='-1 (随机)', --device='cpu', --save-mask='False', --manual-mask='False', --no-controlnet='False', --controlnet-type='`canny`')
        self.assertEqual(result.get("status"), "success")
        self.assertIn("result", result)

    def test_skill_metadata(self):
        """测试技能元数据"""
        self.assertEqual(self.skill.name, "Remove Clothes Skill")
        self.assertIsInstance(self.skill.version, str)


if __name__ == "__main__":
    unittest.main()