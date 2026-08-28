"""
sd_image_generator 单元测试
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from skills.sd_image_generator.skill import SdImageGenerator


class TestSdImageGenerator(unittest.TestCase):
    """
    SdImageGenerator 测试类
    """

    def setUp(self):
        """测试前准备"""
        self.skill = SdImageGenerator()

    def test_execute_with_valid_params(self):
        """测试正常执行"""
        result = self.skill.execute(prompt="", negative_prompt="", model_name='sd-v1-5-tiny.safetensors', width='512', height='512', steps='20', cfg_scale='7.0', seed='-1', output_dir='./generated_images', batch_size='1', scheduler='ddim')
        self.assertEqual(result.get("status"), "success")
        self.assertIn("result", result)

    def test_skill_metadata(self):
        """测试技能元数据"""
        self.assertEqual(self.skill.name, "sd_image_generator")
        self.assertIsInstance(self.skill.version, str)


if __name__ == "__main__":
    unittest.main()