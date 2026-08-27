# photo_restorer

> 老照片修复工具 - 使用AI技术修复、上色、增强老照片

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 12
- **支持模型**: 4+

## 支持的功能

| 功能 | 说明 |
|------|------|
| 🖼️ 照片修复 | 修复破损、划痕、噪点 |
| 🎨 智能上色 | 黑白照片自动上色 |
| 🔍 超分辨率 | 提升照片清晰度和分辨率 |
| 👤 人脸修复 | 专门优化人脸细节 |
| 🤖 多模型支持 | 可切换不同AI引擎 |
| 📁 批量处理 | 支持批量修复多张照片 |

## 支持的AI模型

| 模型 | 类型 | 说明 | 适用场景 |
|------|------|------|----------|
| `real_esrgan` | GAN | 通用图像增强与超分辨率 | 模糊、有噪点的照片 |
| `gfpgan` | GAN | 人脸修复专用 | 人物照片、集体照 |
| `ssdiff` | Diffusion | 扩散模型修复 | 严重破损、大面积缺失 |
| `dcal_gan` | GAN | 细节与结构平衡 | 风景、复杂场景 |

## 依赖安装

```bash
# 基础依赖
pip install opencv-python torch

# AI模型依赖
pip install basicsr gfpgan realesrgan
```

## 使用方法

## 基础修复
```bash
# 使用默认模型修复照片
python -m markflow.cli.commands execute photo_restorer image_path="old_photo.jpg"

# 指定输出目录
python -m markflow.cli.commands execute photo_restorer image_path="old_photo.jpg" output_dir="./restored/"
```

## 选择模型
```bash
# 使用人脸修复模型
python -m markflow.cli.commands execute photo_restorer image_path="family.jpg" model="gfpgan"

# 使用扩散模型修复严重破损
python -m markflow.cli.commands execute photo_restorer image_path="damaged.jpg" model="ssdiff"
```

## 高级参数
```bash
# 4倍放大 + 去噪
python -m markflow.cli.commands execute photo_restorer image_path="old.jpg" scale=4 denoise=true

# 仅增强，不放大
python -m markflow.cli.commands execute photo_restorer image_path="old.jpg" scale=1
```

## 其他操作
```bash
# 查看支持的模型
python -m markflow.cli.commands execute photo_restorer action=list_models

# 查看修复状态
python -m markflow.cli.commands execute photo_restorer action=status
```

## 示例

## 修复一张50年前的黑白全家福
```bash
python -m markflow.cli.commands execute photo_restorer image_path="family_1970.jpg" model="gfpgan"
```


## 批量修复多张照片

```bash
# 方式1：使用 batch_restore action
python -m markflow.cli.commands execute photo_restorer action=batch_restore image_paths='["photo1.jpg","photo2.jpg","photo3.jpg"]'

# 方式2：从文件读取列表
python -m markflow.cli.commands execute photo_restorer action=batch_restore image_paths='$(cat image_list.txt | jq -R -s -c 'split("\n")[:-1]')'
```

## 给黑白照片上色
```bash
# 使用 DeOldify 模型上色
python -m markflow.cli.commands execute photo_restorer image_path="bw_photo.jpg" model="deoldify"

# 或使用 SSDiff 模型
python -m markflow.cli.commands execute photo_restorer image_path="bw_photo.jpg" model="ssdiff"
```
## 📊 最终文件结构总览
```text
skills/photo_restorer/
├── meta.json ✅ 技能元数据
├── README.md ✅ 完整文档
├── skill.py ✅ 核心实现代码
└── output/ 📁 输出目录（运行时自动创建）
├── restored_*.png
├── restore.log
└── favorites.json
```

## 🚀 快速测试

```bash
# 1. 查看支持的模型
python -m markflow.cli.commands execute photo_restorer action=list_models

# 2. 修复一张照片（需要先安装依赖和下载模型）
python -m markflow.cli.commands execute photo_restorer image_path="old_photo.jpg"

# 3. 使用人脸修复模型
python -m markflow.cli.commands execute photo_restorer image_path="family.jpg" model="gfpgan"

# 4. 4倍放大 + 去噪
python -m markflow.cli.commands execute photo_restorer image_path="old.jpg" scale=4 denoise=true

# 5. 查看处理状态
python -m markflow.cli.commands execute photo_restorer action=status
```

## 🧠 技术原理详解

### 1. GAN（生成对抗网络）

GAN 通过生成器与判别器的对抗训练，能够生成高质量、细节丰富的图像。

#### Real-ESRGAN
- **核心改进**: 在 ESRGAN 基础上引入 **高阶退化模型**，模拟真实世界的多种图像退化（模糊、噪声、压缩失真等）
- **技术亮点**: 
  - 使用 **RRDBNet** 作为生成器架构
  - 引入 **感知损失** 和 **对抗损失** 保持视觉真实感
  - 支持 2x/4x 超分辨率放大
- **最佳场景**: 整体模糊、有噪点、分辨率低的照片

#### GFPGAN
- **核心技术**: 利用 **预训练的人脸生成模型**（如 StyleGAN2）作为先验知识
- **技术亮点**:
  - **通道注意力机制** 精确识别面部特征
  - **特征融合** 技术平衡真实感与清晰度
  - 无需对齐即可处理任意角度的人脸
- **最佳场景**: 集体照、面部模糊、五官不清晰的照片

### 2. 扩散模型（Diffusion）

扩散模型通过 **逐步去噪** 的过程生成图像，从纯噪声开始，逐步恢复出清晰的图像。

#### SSDiff (Stable Diffusion 修复变体)
- **核心原理**: 
  1. **前向过程**: 逐步向图像添加噪声，直到变成纯噪声
  2. **反向过程**: 学习去噪网络，从噪声中重建图像
- **技术优势**:
  - **创造性修复**: 能"想象"出缺失的内容
  - **全局一致性**: 修复区域与周围环境自然融合
  - **可控性强**: 可以通过文本提示引导修复方向
- **最佳场景**: 大面积破损、内容缺失、黑白照片上色

### 3. 技术选型对比

| 维度 | GAN (Real-ESRGAN/GFPGAN) | 扩散模型 (SSDiff) |
|------|--------------------------|-------------------|
| **修复速度** | ⚡ 快 (秒级) | 🐢 慢 (分钟级) |
| **细节还原** | ✅ 优秀 | ⭐ 卓越 |
| **创意修复** | ❌ 较差 | ⭐ 优秀 |
| **人脸修复** | ⭐ 专项优化 | ✅ 一般 |
| **GPU内存** | 4-6 GB | 8-12 GB |
| **适用场景** | 清晰化、去噪 | 破损修复、上色 |

## ⚙️ 高级配置

### 完整配置参数

```yaml
# skills/photo_restorer/config.yaml

# ===== 模型配置 =====
model:
  default: "real_esrgan"        # 默认修复模型
  weights_dir: "./models"       # 模型权重存放目录

# ===== 修复参数 =====
restore:
  scale: 2                      # 放大倍数: 1(不放大), 2, 4
  denoise: true                 # 是否启用去噪
  face_enhance: false           # 是否增强面部（GFPGAN专用）
  tile_size: 0                  # 分块处理大小（0=不分块，内存不足时设为512）
  
# ===== 性能配置 =====
performance:
  gpu: true                     # 启用GPU加速
  gpu_id: 0                     # GPU设备ID
  half_precision: false         # 使用半精度（节省内存，略微降低质量）
  batch_size: 1                 # 批量处理大小

# ===== 输出配置 =====
output:
  dir: "./skills/photo_restorer/output"
  format: "png"                 # 输出格式: png, jpg, webp
  quality: 95                   # JPEG质量 (1-100)
  save_original: false          # 是否同时保存原始图像

# ===== 日志配置 =====
logging:
  level: "INFO"                 # DEBUG, INFO, WARNING, ERROR
  file: "restore.log"
  max_size: "10MB"              # 日志文件最大大小
```

