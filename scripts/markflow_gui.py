#!/usr/bin/env python
"""
MarkFlow GUI 启动脚本
"""

import sys
from pathlib import Path

# ✅ 确保项目路径在 sys.path 中
project_root = Path(__file__).parent.parent  # 改为 parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from markflow.gui.launcher import main

if __name__ == "__main__":
    main()